# Generated by Django 2.0.7 on 2018-12-06 21:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0006_auto_20181206_2114'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'permissions': (('view_notification', 'Can view notification'),), 'verbose_name': 'Notification', 'verbose_name_plural': 'Notifications'},
        ),
    ]