# Generated by Django 2.0.7 on 2020-01-03 20:32

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0005_auto_20200102_1943'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalmonthlyreport',
            name='what_converts_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='monthlyreport',
            name='what_converts_data',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
