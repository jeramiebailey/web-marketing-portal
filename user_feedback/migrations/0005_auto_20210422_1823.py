# Generated by Django 2.2 on 2021-04-22 18:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_feedback', '0004_auto_20190418_2003'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userfeedback',
            options={'permissions': (('view_userfeedback__dep', 'View User Feedback Deprecated'),), 'verbose_name': 'User Feedback', 'verbose_name_plural': 'User Feedback'},
        ),
    ]
