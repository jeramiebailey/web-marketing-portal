# Generated by Django 2.0.7 on 2019-08-12 18:25

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content_management', '0066_auto_20190802_1650'),
    ]

    operations = [
        migrations.AddField(
            model_name='articletemplate',
            name='poster',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='defaultPoster', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalarticletemplate',
            name='poster',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
