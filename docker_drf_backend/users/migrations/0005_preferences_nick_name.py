# Generated by Django 2.0.7 on 2019-05-10 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20190509_1312'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='nick_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]