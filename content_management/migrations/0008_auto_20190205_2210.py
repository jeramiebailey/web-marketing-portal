# Generated by Django 2.0.7 on 2019-02-05 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0007_auto_20190205_2135'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentarticle',
            name='keywords',
            field=models.ManyToManyField(blank=True, to='content_management.KeywordMeta'),
        ),
    ]
