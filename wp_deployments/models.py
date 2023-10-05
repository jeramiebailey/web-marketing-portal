from django.db import models
from organizations.models import Organization
from client_onboarding.models import WebsiteBuild
import uuid
from simple_history.models import HistoricalRecords
import os
from .utils import execute_remote_command, execute_local_command, get_app_db_backups, get_app_codebase_backups, delete_github_repo
import datetime
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings

class WebApp(models.Model):
    organization = models.ForeignKey(Organization, related_name="web_applications", null=True, blank=True, on_delete=models.SET_NULL)
    new_build = models.OneToOneField(WebsiteBuild, related_name="new_application", null=True, blank=True, on_delete=models.SET_NULL)
    alias = models.CharField(max_length=255, default="New Web Application")
    site_name = models.CharField(max_length=255, default="newwebapp.com")
    staging_db_name = models.CharField(max_length=255, null=True, blank=True)
    staging_wordpress_db_user = models.CharField(max_length=255, null=True, blank=True)
    staging_wordpress_db_password = models.CharField(max_length=255, null=True, blank=True)
    staging_url = models.URLField(null=True, blank=True)
    production_url = models.URLField(null=True, blank=True)
    github_repo = models.CharField(max_length=500, null=True, blank=True)
    s3_directory = models.CharField(max_length=500, null=True, blank=True)
    github_repo = models.CharField(max_length=500, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    initialization_complete = models.BooleanField(blank=True, default=False)
    last_backup = models.DateTimeField(auto_now=False, null=True)
    active = models.BooleanField(blank=True, default=True)
    scheduled_for_deletion = models.BooleanField(blank=True, default=False)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Web Application"
        verbose_name_plural = "Web Applications"
        permissions = (
            ('view_webapp__dep', 'View Web Application Deprecated'),
            ('execute_command', 'Execute Remote Command'),
        )

    def get_api_view_name(self):
        api_view_name = 'web_applications'
        return api_view_name
    
    def start_app(self):
        command = execute_remote_command(self.site_name, "make start")
        return True
    
    def stop_app(self):
        command = execute_remote_command(self.site_name, "make stop")
        return command

    def backup(self):
        command = execute_remote_command(self.site_name, f"make push_remote S3_BUCKET_DIRECTORY='{self.s3_directory[:-1]}' APPLICATION_ID='{self.uuid}'")
        if command is True:
            self.last_backup = datetime.datetime.now()
            self.save()
        return command
    
    # def check_webserver_status(self):
    #     formatted_site_name = self.site_name.replace('.', '')
    #     container_name = f'{formatted_site_name}_wordpress_webserver_1'
    #     command = execute_remote_command(self.site_name, f"docker inspect -f '{{.State.Running}}' {container_name}")
    #     return command
    
    def check_wordpress_status(self):
        formatted_site_name = self.site_name.replace('.', '')
        container_name = f'{formatted_site_name}_wordpress_php_1'
        command = execute_remote_command(self.site_name, f"docker inspect -f '{{.State.Running}}' {container_name}")
        return command

    def check_website_status(self):
        command = execute_local_command(f'if curl -s --head  --request GET {self.staging_url} | grep "200 OK" > /dev/null; then\nreturn 0\nelse\nreturn 1\nfi;')
        return command

    def get_db_backups(self):
        backups = get_app_db_backups(self.site_name)
        return backups
    
    def get_code_backups(self):
        backups = get_app_codebase_backups(self.site_name, self.uuid)
        return backups

    # NOTE: This is a dangerous and irreversible action
    def clean_app(self, delete_repo=False):
        if delete_repo:
            try:
                delete_git_repo = delete_github_repo(self.site_name)
                delete_git_repo_success = True
            except:
                delete_git_repo_success = False
                raise
        else:
            delete_git_repo_success = True
        try:  
            clean_remote_repo = execute_remote_command(self.site_name, 'sudo make clean')
            clean_remote_repo_success = True
        except:
            clean_remote_repo_success = False
            raise
        try:
            delete_remote_repo = execute_remote_command(self.site_name, f'cd .. && rm -rf {self.site_name}')
            delete_remote_repo_success = True
            print(f'deleted repo ${delete_remote_repo_success}')
        except:
            delete_remote_repo_success = False
            print(f'deleted repo ${delete_remote_repo_success}')
            raise
        # TODO: delete_s3_bucket
        # TODO: delete_route53_domain

        if delete_git_repo_success and clean_remote_repo_success and delete_remote_repo_success:
            return True
        else:
            return False


    def __str__(self):
        if self.organization:
            return f"{self.organization.dba_name}: {self.alias}"
        else:
            return f"{self.alias}"

class ChildTheme(models.Model):
    theme_name = models.CharField(max_length=255)
    zip_file = models.FileField(upload_to='uploads/genesis-child-themes/')
    screenshot = models.ImageField(upload_to='uploads/genesis-child-themes/screenshots/', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    available = models.BooleanField(blank=True, default=True)

    class Meta:
        verbose_name = "Child Theme"
        verbose_name_plural = "Child Themes"
        permissions = (
            ('view_childtheme__dep', 'View Child Themes Deprecated'),
        )

    @property
    def zip_filename(self):
        return os.path.basename(self.zip_file.name)

    def __str__(self):
        return f"{self.theme_name}"