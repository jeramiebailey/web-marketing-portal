# Generated by Django 2.0.7 on 2019-02-21 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0008_auto_20190221_1534'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
