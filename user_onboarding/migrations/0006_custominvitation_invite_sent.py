# Generated by Django 2.0.7 on 2019-03-26 18:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_onboarding', '0005_auto_20190326_1824'),
    ]

    operations = [
        migrations.AddField(
            model_name='custominvitation',
            name='invite_sent',
            field=models.BooleanField(default=False),
        ),
    ]
