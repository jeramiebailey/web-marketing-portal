# Generated by Django 2.0.7 on 2019-01-31 19:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content_management', '0002_auto_20190129_1914'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentarticle',
            name='anchor_1',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='contentarticle',
            name='anchor_2',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='contentarticle',
            name='url_1',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contentarticle',
            name='url_2',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contentkeywords',
            name='cost_per_click',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='contentkeywords',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_keywords', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contentkeywords',
            name='difficulty',
            field=models.PositiveSmallIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='contentkeywords',
            name='volume',
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]