# Generated by Django 2.0.7 on 2018-12-06 21:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0003_auto_20181206_2054'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'permissions': (('view_notification', 'Can view notification'),), 'verbose_name': 'Notification', 'verbose_name_plural': 'Notifications'},
        ),
    ]
