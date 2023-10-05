# Generated by Django 2.0.7 on 2019-04-18 20:03

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0010_auto_20190312_2058'),
        ('content_management', '0054_auto_20190410_1502'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentRequirement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveSmallIntegerField(default=1)),
                ('year', models.IntegerField(default=2019, validators=[django.core.validators.MinValueValidator(2017), django.core.validators.MaxValueValidator(2050)])),
                ('month', models.PositiveSmallIntegerField(choices=[(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'), (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')], default=4)),
                ('month_count', models.SmallIntegerField(default=-1)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_requirements', to='content_management.ContentType')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='org_content_requirements', to='organizations.Organization')),
            ],
            options={
                'verbose_name': 'Content Requirement',
                'verbose_name_plural': 'Content Requirements',
                'permissions': (('view_contentrequirement', 'View Content Requirement'),),
            },
        ),
    ]