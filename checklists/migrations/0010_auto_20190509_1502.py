# Generated by Django 2.0.7 on 2019-05-09 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checklists', '0009_historicalmasterchecklisttemplate_masterchecklisttemplate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checklistitem',
            name='order',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='checklisttemplateitem',
            name='order',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='historicalchecklistitem',
            name='order',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='historicalchecklisttemplateitem',
            name='order',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]