# Generated by Django 2.0.7 on 2019-03-19 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0042_contentarticle_poster'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentarticle',
            name='writer_planned_duedate',
            field=models.DateField(blank=True, null=True),
        ),
    ]