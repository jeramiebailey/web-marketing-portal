from django.db import models
from simple_history.models import HistoricalRecords
from docker_drf_backend.users.models import User
from .constants import REPORT_STATUSES
from presentations.models import SlideDeckTemplate, SlideDeck
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from api.utils import get_report_data, get_whatconverts_data, get_ga4_report_data
from reporting.utils import AhrefsReportScraper, scrape_ahrefs_screenshots
from django.contrib.postgres.fields import JSONField
from docker_drf_backend.users.models import UserOrgRole
import uuid
import calendar
from django.conf import settings
from docker_drf_backend.utils import send_email, send_test_email
from django.contrib.sites.models import Site
from guardian.shortcuts import assign_perm, remove_perm
from datetime import datetime
from django.utils import timezone
import pytz
from django.utils.timezone import make_aware

tz = settings.TIME_ZONE
now = make_aware(datetime.now())

class ReportEmailEntry(models.Model):
    email = models.EmailField(max_length=200, null=True, blank=True)
    report = models.ForeignKey('MonthlyReport', related_name="email_entries", null=True, blank=True, on_delete=models.CASCADE)
    link_clicked = models.BooleanField(blank=True, default=False)
    did_unsubscribe = models.BooleanField(blank=True, default=False)
    date_unsubscribed = models.DateTimeField(null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_sent = models.DateTimeField(auto_now_add=True, null=True)
    date_first_viewed = models.DateTimeField(null=True)

    def get_user(self):
        user_email = self.email
        try:
            corresponding_user = User.objects.get(email=user_email)
        except:
            corresponding_user = None
        if corresponding_user:
            return corresponding_user
        else:
            return None

    def save(self, *args, **kwargs):
        if self.pk:
            previous_instance = ReportEmailEntry.objects.get(pk=self.pk)
        else:
            previous_instance = None
        if previous_instance:
            if previous_instance.link_clicked == False and self.link_clicked == True:
                if not self.date_first_viewed:
                    self.date_first_viewed = now
            if previous_instance.did_unsubscribe == False and self.did_unsubscribe == True:
                if not self.date_unsubscribed:
                    self.date_unsubscribed = now
        super(ReportEmailEntry, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Report Email Entry"
        verbose_name_plural = "Report Email Entries"
        ordering = ['date_sent',]

    def __str__(self):
        return f'{self.email} | {self.uuid}'

class MonthlyReport(models.Model):
    organization = models.ForeignKey('organizations.Organization', related_name="org_monthly_reports", null=True, blank=True, on_delete=models.CASCADE)
    month = models.ForeignKey('content_management.PlanningYearMonth', related_name="related_reports", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(choices=REPORT_STATUSES, max_length=100, blank=True, default='backlog')
    creator = models.ForeignKey('users.User', related_name="assigned_reports", null=True, blank=True, on_delete=models.SET_NULL)
    approver = models.ForeignKey('users.User', related_name="assigned_approval_reports", null=True, blank=True, on_delete=models.SET_NULL)
    report_url = models.URLField(max_length=500, blank=True, null=True)
    presentation = models.ForeignKey(SlideDeck, related_name="corresponding_reports", null=True, blank=True, on_delete=models.SET_NULL)
    google_analytics_data = JSONField(null=True, blank=True)
    what_converts_data = JSONField(null=True, blank=True)
    referring_domains_screenshot = models.ImageField(upload_to='report-screenshots/', null=True, blank=True)
    referring_pages_screenshot = models.ImageField(upload_to='report-screenshots/', null=True, blank=True)
    organic_keywords_screenshot = models.ImageField(upload_to='report-screenshots/', null=True, blank=True)
    detailed_organic_keywords_screenshot = models.ImageField(upload_to='report-screenshots/', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True) 
    history = HistoricalRecords() 

    def get_api_view_name(self):
        api_view_name = 'monthly_reports'
        return api_view_name

    def create_monthly_report_presentation(self):
        try:
            organization_slide_deck_template = self.organization.monthly_report_template
        except ValidationError as e:
            import itertools
            organization_slide_deck_template = None
            errors = list( itertools.chain( *e.message_dict.values() ) )


        if organization_slide_deck_template:
            old_presentation = self.presentation

            if organization_slide_deck_template.use_dynamic_title:
                presentation_name = f'{self.month.get_year_month_verbose()} SEO Briefing'
            else:
                presentation_name = organization_slide_deck_template.name

            new_presentation = organization_slide_deck_template.create_slide_deck(
                name=presentation_name,
                slide_deck_object_type=ContentType.objects.get_for_model(self),
                slide_deck_object_id=self.id
            )
            self.presentation = new_presentation
            self.save()

            org_users = UserOrgRole.objects.select_related('organization', 'user').filter(organization=self.organization)
            new_presentation_slides = new_presentation.slides.all()

            for org_user in org_users:
                assign_perm('view_slidedeck', org_user.user, new_presentation)
                assign_perm('view_slide', org_user.user, new_presentation_slides)

            if old_presentation:
                try:
                    old_presentation.delete()
                except:
                    pass

            return new_presentation

    def get_google_analytics_data(self):
        google_analytics_id = self.organization.google_analytics_id
        report_month = self.month.month
        report_year = self.month.year

        if google_analytics_id:
            try:
                ga_data = get_report_data(view_id=google_analytics_id, start_month=report_month, start_year=report_year)
            except:
                ga_data = None
            if not ga_data:
                try:
                    ga_data = get_ga4_report_data(property_id=google_analytics_id, start_month=report_month, start_year=report_year)
                except:
                    ga_data = None
                    
            if ga_data:
                self.google_analytics_data = ga_data
                self.save()
            else:
                print(f'ga_data call failed with organization: {self.organization.dba_name}')

            return ga_data

    def get_what_converts_data(self):
        what_converts_account = self.organization.what_converts_account
        report_month = self.month.month
        report_year = self.month.year

        if what_converts_account:
            account_id = what_converts_account.account_id
            spt_account = what_converts_account.spt_account

            if account_id:
                wc_data = get_whatconverts_data(
                    account_id=account_id,
                    start_month=report_month,
                    start_year=report_year,
                    spt_account=spt_account,
                )
                self.what_converts_data = wc_data
                self.save()

                return wc_data


    def get_ahrefs_screenshots(self, delay_method=False):
        if self.organization.domain:
            report_id = self.id

            if not delay_method:
                try:
                    ahrefs_data = scrape_ahrefs_screenshots(report_id=report_id)
                    get_reports_success = True
                except:
                    ahrefs_data = None
                    get_reports_success = False

                return ahrefs_data
            else:
                scrape_ahrefs_screenshots.delay(report_id=report_id)

        else:
            return 'Report organization does not have an associated domain.'

    
    def pull_all_report_data(self, pull_screenshots=False):
        if self.organization and self.organization.report_required and self.organization.is_active:
            ga_data = self.get_google_analytics_data()
            wc_data = self.get_what_converts_data()
            if pull_screenshots:
                ahrefs_data = self.get_ahrefs_screenshots(delay_method=True)

            return self


    def send_report_notification(self, is_test=None, is_debug=False): 
        if self.organization and self.organization.business_email:
            if self.status == 'finalReview' or self.status == "sent":
                planning_month = calendar.month_name[self.month.month]
                frontend_url = settings.FRONTEND_URL
                backend_url = settings.BACKEND_URL
                if self.presentation:
                    button_url = f'{frontend_url}/reporting/{self.month.year}/{self.month.month}/{self.organization.slug}'
                elif self.report_url:
                    button_url = f'{self.report_url}'
                else:
                    print('Report does not have a presentation or report_url')
                    return self
                button_text = 'View Your Report Here'
                subject = f'Monthly 321 Web Marketing Report for {planning_month} {self.month.year}'
                template = 'reporting/monthly_report.html'
                business_email = self.organization.business_email
                recipients = UserOrgRole.objects.select_related('organization', 'user').filter(organization=self.organization, receive_reporting_email=True)
                recipient_list = []
                if recipients.first():
                    for recipient in recipients:
                        email = recipient.user.email
                        recipient_list.append(email)
                else:
                    if business_email:
                        recipient_list.append(business_email)

                if not is_test:
                    # print('send_report_notification is not test')
                    if recipient_list and recipient_list[0]:
                        for recipient in recipient_list:
                            # print('send_report_notification is recipient')
                            to_email = [recipient,]
                            new_report_email_entry = ReportEmailEntry.objects.create(email=recipient, report=self)
                            unsubcribe_url = f'{backend_url}/reporting/unsubscribe/{new_report_email_entry.uuid}/{recipient}'
                            complete_button_url = button_url
                            complete_button_url += f'?entryID={new_report_email_entry.id}'
                            email_context = { 
                                'company_name': self.organization.dba_name,
                                'email': self.organization.business_email,
                                'planning_month': planning_month,
                                'planning_year': self.month.year,
                                'button_text': button_text,
                                'button_url': complete_button_url,
                                'unsubcribe_url': unsubcribe_url,
                            }

                            # reporting_email = send_email(
                            #         template=template,
                            #         recipients=to_email,
                            #         subject=subject,
                            #         context=email_context,
                            #         meta_data={"report_email_uuid": new_report_email_entry.uuid},
                            #         debug=is_debug,
                            #     )
                            reporting_email = send_email.delay(
                                    template=template,
                                    recipients=to_email,
                                    subject=subject,
                                    context=email_context,
                                    meta_data={"report_email_uuid": new_report_email_entry.uuid},
                                    debug=is_debug,
                                )
                            self.status = 'sent'
                            # print('send_report_notification status should be sent')
                            self.save()
                
                else:
                    email_context = { 
                            'company_name': self.organization.dba_name,
                            'email': self.organization.business_email,
                            'planning_month': planning_month,
                            'planning_year': self.month.year,
                            'button_text': button_text,
                            'button_url': button_url,
                        }
                    reporting_email = send_test_email(
                                template=template,
                                subject=subject,
                                context=email_context,
                            )

                return self

    class Meta:
        unique_together = (("organization", "month"))
        verbose_name = "Monthly Report"
        verbose_name_plural = "Monthly Reports"
        permissions = (
            ('view_monthlyreport__dep', 'View Monthly Report Deprecated'),
        )

    def __str__(self):
        return f'{self.id}'

