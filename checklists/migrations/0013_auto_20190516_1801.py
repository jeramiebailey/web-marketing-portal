# Generated by Django 2.0.7 on 2019-05-16 18:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0012_auto_20190516_1757'),
    ]

    operations = [
        migrations.RenameField(
            model_name='checklisttemplateitem',
            old_name='days',
            new_name='days_out',
        ),
        migrations.RenameField(
            model_name='historicalchecklisttemplateitem',
            old_name='days',
            new_name='days_out',
        ),
    ]