# Generated by Django 2.0.7 on 2019-07-18 19:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('content_management', '0065_auto_20190717_1418'),
        ('organizations', '0010_auto_20190312_2058'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalMonthlyReport',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('status', models.CharField(blank=True, choices=[('backlog', 'Backlog'), ('assigned', 'Assigned'), ('finalReview', 'Final Review'), ('sent', 'Sent')], default='backlog', max_length=100)),
                ('report_url', models.URLField(blank=True, max_length=500, null=True)),
                ('date_created', models.DateTimeField(blank=True, editable=False)),
                ('last_updated', models.DateTimeField(blank=True, editable=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('approver', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('creator', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('month', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='content_management.PlanningYearMonth')),
                ('organization', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='organizations.Organization')),
            ],
            options={
                'verbose_name': 'historical Monthly Report',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='MonthlyReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(blank=True, choices=[('backlog', 'Backlog'), ('assigned', 'Assigned'), ('finalReview', 'Final Review'), ('sent', 'Sent')], default='backlog', max_length=100)),
                ('report_url', models.URLField(blank=True, max_length=500, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('approver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_approval_reports', to=settings.AUTH_USER_MODEL)),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_reports', to=settings.AUTH_USER_MODEL)),
                ('month', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_reports', to='content_management.PlanningYearMonth')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='org_monthly_reports', to='organizations.Organization')),
            ],
            options={
                'verbose_name': 'Monthly Report',
                'verbose_name_plural': 'Monthly Reports',
                'permissions': (('view_monthlyreport', 'View Monthly Report'),),
            },
        ),
    ]
