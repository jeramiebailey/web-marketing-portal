# Generated by Django 2.0.7 on 2019-09-25 16:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0069_auto_20190909_1449'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentproject',
            name='complete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalcontentproject',
            name='complete',
            field=models.BooleanField(default=False),
        ),
    ]
