# Generated by Django 2.0.7 on 2019-06-05 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wp_deployments', '0005_auto_20190604_1757'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='webapp',
            options={'permissions': (('view_webapp', 'View Web Application'), ('execute_command', 'Execute Remote Command')), 'verbose_name': 'Web Application', 'verbose_name_plural': 'Web Applications'},
        ),
        migrations.AddField(
            model_name='childtheme',
            name='screenshot',
            field=models.ImageField(blank=True, null=True, upload_to='uploads/genesis-child-themes/screenshots/'),
        ),
        migrations.AddField(
            model_name='historicalwebapp',
            name='last_backup',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='webapp',
            name='last_backup',
            field=models.DateTimeField(null=True),
        ),
    ]
