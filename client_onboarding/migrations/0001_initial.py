# Generated by Django 2.0.7 on 2019-04-24 21:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('checklists', '0009_historicalmasterchecklisttemplate_masterchecklisttemplate'),
        ('organizations', '0010_auto_20190312_2058'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalWebsiteBuild',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(blank=True, editable=False, null=True)),
                ('last_updated', models.DateTimeField(blank=True, editable=False, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('build_checklist', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='checklists.Checklist')),
                ('deploy_checklist', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='checklists.Checklist')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='organizations.Organization')),
            ],
            options={
                'verbose_name': 'historical Website Build',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='WebsiteBuild',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('build_checklist', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='website_build_checklists', to='checklists.Checklist')),
                ('deploy_checklist', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='website_deploy_checklists', to='checklists.Checklist')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='org_website_builds', to='organizations.Organization')),
            ],
            options={
                'verbose_name': 'Website Build',
                'verbose_name_plural': 'Website Builds',
                'permissions': (('view_websitebuild', 'View Website Builds'),),
            },
        ),
    ]