# Generated by Django 2.0.7 on 2019-07-19 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_preferences_nick_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='userorgrole',
            name='receive_reporting_email',
            field=models.BooleanField(default=False),
        ),
    ]
