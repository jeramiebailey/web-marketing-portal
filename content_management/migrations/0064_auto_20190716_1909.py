# Generated by Django 2.0.7 on 2019-07-16 19:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0063_auto_20190715_1624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='planningyearmonth',
            name='default_status',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_default_months', to='content_management.ContentStatus'),
        ),
    ]