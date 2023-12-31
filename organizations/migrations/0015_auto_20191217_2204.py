# Generated by Django 2.0.7 on 2019-12-17 22:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0014_organization_monthly_report_template'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='monthly_report_template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='corresponding_org_report_template', to='presentations.SlideDeckTemplate'),
        ),
    ]
