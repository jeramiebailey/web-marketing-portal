from django.db import models
from organizations.models import Organization
from checklists.models import Checklist
from simple_history.models import HistoricalRecords

class WebsiteBuild(models.Model):
    label = models.CharField(max_length=255, null=True, blank=True)
    organization = models.ForeignKey(Organization, related_name="org_website_builds", on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    start_date = models.DateField(blank=True, null=True)
    brand_interview_link = models.URLField(max_length=255, null=True, blank=True)
    sitemap_link = models.URLField(max_length=255, null=True, blank=True)
    staging_url = models.URLField(max_length=255, null=True, blank=True)
    intake_link = models.URLField(max_length=255, null=True, blank=True)
    build_checklist = models.ForeignKey(Checklist, null=True, blank=True, related_name="website_build_checklists", on_delete=models.SET_NULL)
    deploy_checklist = models.ForeignKey(Checklist, null=True, blank=True, related_name="website_deploy_checklists", on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    history = HistoricalRecords()

    def get_api_view_name(self):
        api_view_name = 'website_builds'
        return api_view_name

    class Meta:
        verbose_name = "Website Build"
        verbose_name_plural = "Website Builds"
        permissions = (
            ('view_websitebuild__dep', 'View Website Builds Deprecated'),
            ('initialize_websitebuild', 'Initialize Website Build')
        )

    def __str__(self):
        return "{} Build".format(self.organization.dba_name)