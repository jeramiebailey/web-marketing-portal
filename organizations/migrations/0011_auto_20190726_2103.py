# Generated by Django 2.0.7 on 2019-07-26 21:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organizations', '0010_auto_20190312_2058'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='default_report_approver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organization_approvals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='organization',
            name='default_report_creator',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organization_report_duties', to=settings.AUTH_USER_MODEL),
        ),
    ]
