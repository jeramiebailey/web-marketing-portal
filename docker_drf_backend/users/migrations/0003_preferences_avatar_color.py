# Generated by Django 2.0.7 on 2019-05-08 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='avatar_color',
            field=models.CharField(blank=True, default='#888888', max_length=10),
        ),
    ]