# Generated by Django 2.0.7 on 2019-12-11 18:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('presentations', '0001_initial'),
        ('organizations', '0013_auto_20190909_1451'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='monthly_report_template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='corresponding_org_report_templates', to='presentations.SlideDeckTemplate'),
        ),
    ]