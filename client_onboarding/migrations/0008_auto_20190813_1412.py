# Generated by Django 2.0.7 on 2019-08-13 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('client_onboarding', '0007_auto_20190730_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalwebsitebuild',
            name='staging_url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='websitebuild',
            name='staging_url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]
