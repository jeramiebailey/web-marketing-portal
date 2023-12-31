# Generated by Django 2.2 on 2021-04-22 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0023_auto_20210330_1741'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'permissions': (('view_address__dep', 'View Address Deprecated'),), 'verbose_name': 'Address', 'verbose_name_plural': 'Addresses'},
        ),
        migrations.AlterModelOptions(
            name='organization',
            options={'ordering': ['dba_name'], 'permissions': (('view_organization__dep', 'View Organization Deprecated'),), 'verbose_name': 'Organization', 'verbose_name_plural': 'Organizations'},
        ),
        migrations.AlterModelOptions(
            name='whatconvertsaccount',
            options={'permissions': (('view_whatconvertsaccount__dep', 'View WhatConverts Account Deprecated'),), 'verbose_name': 'WhatConverts Account', 'verbose_name_plural': 'WhatConverts Accounts'},
        ),
        migrations.AlterField(
            model_name='organization',
            name='is_active',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='report_required',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name='whatconvertsaccount',
            name='report_calls',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name='whatconvertsaccount',
            name='report_chats',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name='whatconvertsaccount',
            name='report_form_fills',
            field=models.BooleanField(blank=True, default=True),
        ),
        migrations.AlterField(
            model_name='whatconvertsaccount',
            name='spt_account',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
