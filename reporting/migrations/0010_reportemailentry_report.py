# Generated by Django 2.0.7 on 2020-01-16 15:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0009_auto_20200115_2152'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportemailentry',
            name='report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='email_entries', to='reporting.MonthlyReport'),
        ),
    ]
