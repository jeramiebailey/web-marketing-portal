# Generated by Django 2.0.7 on 2019-04-02 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0050_auto_20190327_1822'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedback',
            name='satisfaction',
            field=models.PositiveSmallIntegerField(blank=True, default=0, null=True),
        ),
    ]