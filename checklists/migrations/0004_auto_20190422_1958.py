# Generated by Django 2.0.7 on 2019-04-22 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0003_auto_20190422_1935'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checklistitem',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='checklisttemplateitem',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='historicalchecklistitem',
            name='order',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='historicalchecklisttemplateitem',
            name='order',
            field=models.IntegerField(default=0),
        ),
    ]
