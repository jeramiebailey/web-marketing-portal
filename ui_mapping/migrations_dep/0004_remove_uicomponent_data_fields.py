# Generated by Django 2.0.7 on 2019-12-16 16:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ui_mapping', '0003_auto_20191216_1639'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='uicomponent',
            name='data_fields',
        ),
    ]
