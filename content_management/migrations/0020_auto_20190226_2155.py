# Generated by Django 2.0.7 on 2019-02-26 21:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content_management', '0019_auto_20190221_1600'),
    ]

    operations = [
        migrations.AlterField(
            model_name='articletemplate',
            name='client',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='defaultOrganizationTemplate', to='organizations.Organization'),
        ),
        migrations.AlterField(
            model_name='articletemplate',
            name='content_channels',
            field=models.ManyToManyField(blank=True, null=True, to='content_management.ContentChannel'),
        ),
        migrations.AlterField(
            model_name='articletemplate',
            name='content_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='defaultContentType', to='content_management.ContentType'),
        ),
        migrations.AlterField(
            model_name='articletemplate',
            name='min_word_count',
            field=models.PositiveSmallIntegerField(null=True),
        ),
    ]
