from django.db import models
from organizations.models import Organization
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from api.utils import get_report_data, get_whatconverts_data, get_ga4_report_data
from django.contrib.postgres.fields import JSONField
from dateutil.relativedelta import *
import datetime
from django.utils import timezone
from guardian.shortcuts import assign_perm, remove_perm
from account_health.utils import get_page_speed_insights, parse_page_speed_insights

UserModel = get_user_model()

class AccountHealth(models.Model):
    account = models.OneToOneField(Organization, related_name="account_health", on_delete=models.CASCADE)
    leads_data = JSONField(null=True, blank=True)
    organic_traffic_data = JSONField(null=True, blank=True)
    desktop_page_speed_data = JSONField(null=True, blank=True)
    mobile_page_speed_data = JSONField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Account Health"
        verbose_name_plural = "Account Health"
        permissions = (
            ('view_accounthealth__dep', 'View Account Health Deprecated'),
        )

    def get_overdue_approvals(self, as_list=False):
        now = timezone.now()
        staff = UserModel.objects.filter(is_staff=True, is_active=True)
        # overdue_approvals = self.account.contentClient.select_related(
        #         'client', 
        #         'status', 
        #         'writer',
        #         'editor',
        #         'poster',
        #         'lead',
        #         'final_approver'
        #     ).prefetch_related('writer__user').filter(status__order=7, archived=False).exclude(final_approver__in=staff)
        overdue_approvals = self.account.contentClient.select_related(
                'client', 
                'status', 
                'writer',
                'editor',
                'poster',
                'lead',
                'final_approver'
            ).prefetch_related('writer__user').filter(status__uid='final_review', archived=False).exclude(final_approver__in=staff)

        if as_list:
            return list(overdue_approvals.values_list('id', flat=True).distinct())
        else:
            return overdue_approvals

    def get_leads_over_time_data(self):
        if self.account.google_analytics_id:
            try:
                data = get_report_data(view_id=self.account.google_analytics_id, months_back=12)
            except:
                data = None
            
            if not data:
                try:
                    data = get_ga4_report_data(property_id=self.account.google_analytics_id, months_back=12)
                except:
                    data = None

            if data:
                self.leads_data = data
                self.save()

                return data
    
    def get_organic_traffic_data(self):
        if self.account.what_converts_account and self.account.what_converts_account.account_id:
            try:
                data = get_whatconverts_data(account_id=self.account.what_converts_account.account_id, spt_account=self.account.what_converts_account.spt_account, months_back=12)
            except:
                data = None

            if data: 
                self.organic_traffic_data = data
                self.save()

                return data

    def get_desktop_page_speed_data(self):
        if self.account.domain:
            try:
                data = parse_page_speed_insights(domain=self.account.domain, strategy='desktop')
            except:
                data = None

            if data:
                self.desktop_page_speed_data = data
                self.save()

                return data
    
    def get_mobile_page_speed_data(self):
        if self.account.domain:
            try:
                data = parse_page_speed_insights(domain=self.account.domain, strategy='mobile')
            except:
                data = None

            if data:
                self.mobile_page_speed_data = data
                self.save()

                return data

    def pull_all_account_data(self):
        self.get_leads_over_time_data()
        self.get_organic_traffic_data()
        self.get_desktop_page_speed_data()
        self.get_mobile_page_speed_data()

    def assign_account_health_permissions(self):
        account_user_roles = list(self.account.user_roles.filter(role__name__in=['Customer', 'Account Owner']).values_list('user__id', flat=True).distinct())
        account_users = UserModel.objects.filter(id__in=account_user_roles)

        assigned_permissions = assign_perm('view_accounthealth', account_users, self)

        return assigned_permissions

    def __str__(self):
        return f'{self.account.dba_name} Account Health'