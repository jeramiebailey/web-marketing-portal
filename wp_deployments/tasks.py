from celery import shared_task
from docker_drf_backend.users.models import User
from .models import WebApp
from .utils import delete_backup_object
from django.core.mail import send_mail
import datetime
import requests
from django.contrib.sites.models import Site
import environ

env = environ.Env()

@shared_task(name="backup_apps")
def backup_apps():
    all_applications = WebApp.objects.filter(active=True)
    for app in all_applications:
        new_backup = app.backup()
        
        current_db_backups = app.get_db_backups()
        current_code_backups = app.get_code_backups()

        current_db_backups_count = len(current_db_backups)
        current_code_backups_count = len(current_code_backups)

        if current_db_backups_count > 14:
            current_db_backups_sorted = sorted(current_db_backups, key = lambda i: i['LastModified'])
            current_code_backups_sorted = sorted(current_code_backups, key = lambda i: i['LastModified'])

            deleted_db_backup = delete_backup_object(current_db_backups_sorted[0]['Key'])
            deleted_code_backup = delete_backup_object(current_code_backups_sorted[0]['Key'])
