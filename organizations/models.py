from django.db import models
from .constants import US_STATE_CHOICES
from django_extensions.db.fields import AutoSlugField
from django.utils.timezone import now
from presentations.models import SlideDeckTemplate
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType

class WhatConvertsAccount(models.Model):
    account_id = models.CharField(max_length=200)
    report_calls = models.BooleanField(blank=True, default=True)
    report_form_fills = models.BooleanField(blank=True, default=True)
    report_chats = models.BooleanField(blank=True, default=True)
    spt_account = models.BooleanField(blank=True, default=False)

    class Meta:
        verbose_name = "WhatConverts Account"
        verbose_name_plural = "WhatConverts Accounts"
        permissions = (
            ('view_whatconvertsaccount__dep', 'View WhatConverts Account Deprecated'),
        )

    def __str__(self):
        return self.account_id

class Organization(models.Model):
    legal_name = models.CharField(max_length=150)
    dba_name = models.CharField(max_length=150, db_index=True)
    slug = AutoSlugField(populate_from='dba_name', blank=True, default="", db_index=True)
    business_email = models.EmailField(max_length=200, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    street_address_1 = models.CharField(max_length=200, null=True, blank=True)
    street_address_2 = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(choices=US_STATE_CHOICES, null=True, blank=True, max_length=100)
    zipcode = models.CharField(max_length=12, blank=True, null=True)
    domain = models.URLField(blank=True, null=True)
    logo = models.FileField(upload_to='uploads/logos/', null=True, blank=True)
    monthly_report_template = models.ForeignKey(SlideDeckTemplate, related_name="corresponding_org_report_templates", null=True, blank=True, on_delete=models.SET_NULL)
    google_analytics_id = models.CharField(max_length=200, null=True, blank=True)
    what_converts_account = models.ForeignKey(WhatConvertsAccount, related_name="wc_organizations", null=True, blank=True, on_delete=models.SET_NULL)
    contract_start_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, default=True)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    report_required = models.BooleanField(blank=True, default=True)
    account_lead = models.ForeignKey('users.User', related_name="responsible_accounts", blank=True, null=True, on_delete=models.SET_NULL)
    project_manager = models.ForeignKey('users.User', related_name="accounts_managed", blank=True, null=True, on_delete=models.SET_NULL)
    default_report_creator = models.ForeignKey('users.User', related_name="organization_report_duties", blank=True, null=True, on_delete=models.SET_NULL)
    default_report_approver = models.ForeignKey('users.User', related_name="organization_approvals", blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        permissions = (
            ('view_organization__dep', 'View Organization Deprecated'),
        )
        ordering = ['dba_name']

    def create_report_template_from_master(self):
        existing_monthly_report_template = self.monthly_report_template
        try:
            master_org_report_template = SlideDeckTemplate.objects.get(content_type=ContentType.objects.get_for_model(self), is_master_template=True)
        except:
            master_org_report_template = None

        if master_org_report_template:
            new_report_template = master_org_report_template.cascade_from_master_template(object_id=self.id, name=f'{self.dba_name} Monthly Report Template', derived_fields=['organization',])

            self.monthly_report_template = new_report_template
            self.save()

            if existing_monthly_report_template:
                existing_monthly_report_template.delete()

            return new_report_template

    def create_whatconverts_account(self, account_id, report_calls, report_form_fills, report_chats, spt_account):
        try:
            new_wc_account = WhatConvertsAccount.objects.create(
                account_id=account_id,
                report_calls=report_calls,
                report_form_fills=report_form_fills,
                report_chats=report_chats,
                spt_account=spt_account,
            )
            new_wc_account_success = True
        except ValidationError as e:
            import itertools
            new_wc_account_success = list( itertools.chain( *e.message_dict.values() ) )

        if new_wc_account_success is True:
            new_wc_account.save()
            if self.what_converts_account:
                self.what_converts_account.delete()
                
            self.what_converts_account = new_wc_account
            self.save()
            return new_wc_account_success
        else:
            return new_wc_account_success

    def get_pending_content_approvals(self, as_list=False):
        pending_approvals = self.contentClient.select_related(
                'client', 
                'status', 
                'writer',
                'editor',
                'poster',
                'lead',
                'final_approver'
            ).prefetch_related('writer__user').filter(status__uid='final_review', archived=False)

        if as_list:
            return list(pending_approvals.values_list('id', flat=True).distinct())
        else:
            return pending_approvals
    

    def __str__(self):
        return str(self.dba_name)


class Address(models.Model):
    organization = models.ForeignKey(Organization, related_name="addresses",  on_delete=models.CASCADE, blank=True)
    name_for_directory = models.CharField(max_length=70, null=True, blank=True)
    street_1 = models.CharField(max_length=100)
    street_2 = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=10, choices=US_STATE_CHOICES)
    zipcode = models.CharField(max_length=10)
    location_phone_number = models.CharField(max_length=50, null=True, blank=True)
    static_tracking_phone_number = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        permissions = (
            ('view_address__dep', 'View Address Deprecated'),
        )

    def __str__(self):
        return "{}: {}, {}".format(self.organization, self.city, self.state)


