# Generated by Django 2.0.7 on 2019-12-05 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0072_auto_20191204_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentkeywords',
            name='difficulty',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
