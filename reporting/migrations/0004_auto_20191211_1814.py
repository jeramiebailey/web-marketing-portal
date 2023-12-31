# Generated by Django 2.0.7 on 2019-12-11 18:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('presentations', '0001_initial'),
        ('reporting', '0003_auto_20190802_1827'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalmonthlyreport',
            name='presentation',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='presentations.SlideDeck'),
        ),
        migrations.AddField(
            model_name='monthlyreport',
            name='presentation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='corresponding_reports', to='presentations.SlideDeck'),
        ),
    ]
