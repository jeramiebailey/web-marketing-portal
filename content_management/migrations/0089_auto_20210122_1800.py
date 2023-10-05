# Generated by Django 2.0.7 on 2021-01-22 18:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0088_auto_20210119_1849'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contentarticle',
            old_name='duedate_scheduled',
            new_name='duedate_schedulepost',
        ),
        migrations.RenameField(
            model_name='contentarticle',
            old_name='duedate_draft',
            new_name='duedate_write',
        ),
        migrations.RenameField(
            model_name='historicalcontentarticle',
            old_name='duedate_scheduled',
            new_name='duedate_schedulepost',
        ),
        migrations.RenameField(
            model_name='historicalcontentarticle',
            old_name='duedate_draft',
            new_name='duedate_write',
        ),
        migrations.RemoveField(
            model_name='contentarticle',
            name='duedate_clientreview',
        ),
        migrations.RemoveField(
            model_name='historicalcontentarticle',
            name='duedate_clientreview',
        ),
    ]