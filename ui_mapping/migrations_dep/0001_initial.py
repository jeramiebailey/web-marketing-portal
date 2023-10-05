# Generated by Django 2.0.7 on 2019-12-13 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UIComponent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Component Name')),
                ('is_allowed', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'UI Component',
                'verbose_name_plural': 'UI Components',
                'permissions': (('view_uicomponent', 'View UI Component'),),
            },
        ),
    ]
