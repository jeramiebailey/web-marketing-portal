# Generated by Django 2.0.7 on 2019-04-10 20:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user_feedback', '0002_auto_20190410_2027'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userfeedback',
            options={'permissions': (('view_userfeedback', 'View User Feedback'),), 'verbose_name': 'User Feedback', 'verbose_name_plural': 'User Feedback'},
        ),
    ]
