# Generated by Django 2.0.7 on 2019-06-07 18:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wp_deployments', '0009_auto_20190607_1357'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalwebapp',
            name='nginx_port',
        ),
        migrations.RemoveField(
            model_name='webapp',
            name='nginx_port',
        ),
    ]
