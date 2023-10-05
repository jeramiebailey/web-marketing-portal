# Generated by Django 2.0.7 on 2019-04-25 18:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('client_onboarding', '0002_auto_20190425_1747'),
    ]

    operations = [
        migrations.AlterField(
            model_name='websitebuild',
            name='build_checklist',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='website_build_checklists', to='checklists.Checklist'),
        ),
        migrations.AlterField(
            model_name='websitebuild',
            name='deploy_checklist',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='website_deploy_checklists', to='checklists.Checklist'),
        ),
    ]