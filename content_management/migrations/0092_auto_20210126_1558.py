# Generated by Django 2.0.7 on 2021-01-26 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0091_auto_20210126_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentarticle',
            name='duedate_schedulepost',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='historicalcontentarticle',
            name='duedate_schedulepost',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
