# Generated by Django 2.0.7 on 2019-02-27 22:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0023_auto_20190227_2207'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentarticle',
            name='channels',
            field=models.ManyToManyField(to='content_management.ContentChannel'),
        ),
    ]