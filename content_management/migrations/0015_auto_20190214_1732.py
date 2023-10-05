# Generated by Django 2.0.7 on 2019-02-14 17:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0006_organization_phone_number'),
        ('content_management', '0014_auto_20190213_2038'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrganizationEditorialRequirement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('requirement', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('last_update', models.DateTimeField(auto_now=True, null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='editorial_requirements', to='organizations.Organization')),
            ],
            options={
                'verbose_name': 'Organization Editorial Requirement',
                'verbose_name_plural': 'Organization Editorial Requirements',
                'permissions': (('view_organizationeditorialrequirement', 'Organization Editorial Requirement'),),
            },
        ),
        migrations.AlterField(
            model_name='contentcomments',
            name='article',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contentComments', to='content_management.ContentArticle'),
        ),
    ]