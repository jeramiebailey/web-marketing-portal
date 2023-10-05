# Generated by Django 2.0.7 on 2019-06-04 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wp_deployments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalwebapp',
            name='github_repo',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='historicalwebapp',
            name='s3_directory',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='webapp',
            name='github_repo',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='webapp',
            name='s3_directory',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]