# Generated by Django 2.0.7 on 2019-05-31 18:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('client_onboarding', '0004_auto_20190516_1712'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='websitebuild',
            options={'permissions': (('view_websitebuild', 'View Website Builds'), ('initialize_websitebuild', 'Initialize Website Build')), 'verbose_name': 'Website Build', 'verbose_name_plural': 'Website Builds'},
        ),
    ]
