# Generated by Django 2.0.7 on 2020-03-24 18:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0078_auto_20200324_1752'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='contentarticlehistoryset',
            unique_together={('year', 'month', 'day')},
        ),
    ]
