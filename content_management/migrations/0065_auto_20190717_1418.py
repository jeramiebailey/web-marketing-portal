# Generated by Django 2.0.7 on 2019-07-17 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0064_auto_20190716_1909'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentproject',
            name='due_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalcontentproject',
            name='due_date',
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
    ]
