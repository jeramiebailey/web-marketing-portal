# Generated by Django 2.0.7 on 2019-05-16 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client_onboarding', '0003_auto_20190425_1833'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalwebsitebuild',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='websitebuild',
            name='start_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]