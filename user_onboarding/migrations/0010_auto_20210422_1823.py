# Generated by Django 2.2 on 2021-04-22 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_onboarding', '0009_auto_20200115_2012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custominvitation',
            name='create_user',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='custominvitation',
            name='invite_sent',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='custominvitation',
            name='is_writer',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterField(
            model_name='custominvitation',
            name='send_invite',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
