# Generated by Django 2.0.7 on 2019-03-26 18:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_onboarding', '0006_custominvitation_invite_sent'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='custominvitation',
            unique_together={('first_name', 'last_name')},
        ),
    ]
