from docker_drf_backend.users.models import UserOrgRole, User, Preferences
from organizations.models import Organization
from content_management.models import OrganizationRequirements, ContentStatus, ContentArticle
from django.contrib.auth.models import Group
from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm
from django.db import transaction
from guardian.models import UserObjectPermission
from django.db.models import Q
from account_health.models import AccountHealth

@receiver(post_save, sender=Organization)
def create_organizational_requirements(sender, instance, created, **kwargs):
    if created:
        try:
            requirements = OrganizationRequirements.objects.create(organization=instance)
        except:
            pass

        try:
            corresponding_account_health = AccountHealth.objects.create(account=instance)
        except:
            print('Did not successfully create Account Health object')
            pass

@receiver(post_save, sender=Organization)
def perform_account_deactivation_cleanup(sender, created, instance, **kwargs):
    if instance.is_active == False:
        # on_hold_status = ContentStatus.objects.get(order=11)
        on_hold_status = ContentStatus.objects.get(uid='on_hold')
        organization_articles = ContentArticle.objects.filter(client__id=instance.id)
        operation = organization_articles.update(status=on_hold_status)