# Generated by Django 2.0.7 on 2018-12-06 20:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0002_auto_20181206_2025'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notification',
            options={'permissions': (('view_notifications', 'Can view notifications'),), 'verbose_name': 'Notification', 'verbose_name_plural': 'Notifications'},
        ),
    ]
