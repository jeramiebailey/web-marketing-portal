# Generated by Django 2.0.7 on 2020-01-02 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0017_auto_20191220_1430'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='google_analytics_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='what_converts_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
