from .models import UserOrgRole, User, Preferences
from organizations.models import Organization
from reporting.models import MonthlyReport
from content_management.models import ContentArticle
from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm
from django.db import transaction
from guardian.models import UserObjectPermission
from django.db.models import Q
from docker_drf_backend.users.tasks import perform_user_offboarding_tasks
from reporting.tasks import assign_report_permissions

# if the instance was updated delete unused roles 
@receiver(post_save, sender=Group)
def delete_group_permissions(sender, created, instance, **kwargs):
    if not created:
        if instance.id:
            associated_roles = UserOrgRole.objects.filter(role=instance)
            old_instance = Group.objects.get(id=instance.id)
            new_instance_perms = instance.permissions.all()
            new_perms = []
            for permission in new_instance_perms:
                new_perms.append(permission.id)
            if associated_roles:
                for user_role in associated_roles:
                    old_permissions = old_instance.permissions.exclude(id__in=new_perms)
                    new_permissions = instance.permissions.filter(id__in=new_perms)
                    for perm in old_permissions:
                        try:
                            with transaction.atomic():
                                remove_perm(perm.codename, user_role.user, user_role.organization)
                        except:
                            pass

# if the instance was updated add new roles
@receiver(post_save, sender=Group)
def update_group_permissions(sender, instance, created, **kwargs):
    if not created:
        associated_roles = UserOrgRole.objects.filter(role=instance)
        if associated_roles:
            for user_role in associated_roles:
                permissions = instance.permissions.all()
                for perm in permissions:
                    if perm:
                        try:
                            with transaction.atomic():
                                assign_perm(perm.codename, user_role.user, user_role.organization)
                        except:
                            pass
        

# add appropriate group to user based on default role after creation
# @receiver(post_save, sender=User)
# def assign_default_role(sender, instance, created, **kwargs):
#     if created:
#         if instance.default_role:
#             try:
#                 with transaction.atomic():
#                     instance.groups.add(instance.default_role)
#             except:
#                 pass
#         Preferences.objects.create(pk=instance.id)

# add appropriate group to user based on default role after updating
@receiver(post_save, sender=User)
def update_default_role(sender, created, instance, **kwargs):
    if created:
        if instance.is_staff:
            tto = Organization.objects.get(pk=1)
            Preferences.objects.create(user=instance, default_organization=tto)
    if instance.default_role:
        try:
            with transaction.atomic():
                group = Group.objects.get(pk=instance.default_role.id)
                group.user_set.add(instance)
        except:
            pass
    # Preferences.objects.get_or_create(pk=instance.id)

# delete and cleanup any unused roles after role deletion
@receiver(post_delete, sender=UserOrgRole)
def remove_obj_perms_connected_with_user(sender, instance, **kwargs):
    print('remove_obj_perms_connected_with_user')
     # get user
    user = instance.user

    # aggregate all current authorized organizations
    orgs = []
    for role in UserOrgRole.objects.filter(user=user):
        orgs.append(role.organization.id)

    # aggregate all updated unauthorized organizations
    unauthorized_orgs = []
    for org in Organization.objects.exclude(pk__in=orgs):
        unauthorized_orgs.append(org.id)

    # filter through all old/unused object permissions and delete them
    filters = Q(content_type=ContentType.objects.get_for_model(Organization),
        object_pk__in=unauthorized_orgs, user=user)
    oldPerms = UserObjectPermission.objects.filter(filters)
    oldPerms.delete()

# add appropriate group and object-level permissions to user after creation
@receiver(post_save, sender=UserOrgRole)
def assign_user_org_roles(sender, instance, created, **kwargs):
    if created:
        instance.user.groups.add(instance.role)
        permissions = instance.role.permissions.filter(content_type=ContentType.objects.get_for_model(Organization))

        # add organization permissions
        for perm in permissions:
            try:
                with transaction.atomic():
                    assign_perm(perm.codename, instance.user, instance.organization)
            except:
                pass

        if instance.organization:
            organization_articles = ContentArticle.objects.filter(client=instance.organization)
            # assign content article permissions
            assign_perm('view_contentarticle', instance.user, organization_articles)
            print('should assign report permissions here')
            assign_report_permissions.delay(instance.user.id)
            # assign_report_permissions(instance.user.id)
            organization_account_health = instance.organization.account_health
            if organization_account_health:
                try:
                    with transaction.atomic():
                        organization_account_health.assign_account_health_permissions()
                except:
                    pass


# add appropriate group and object-level permissions to user after updating
@receiver(pre_save, sender=UserOrgRole)
def update_user_org_roles(sender, instance, **kwargs):
    try:
        old_instance = UserOrgRole.objects.get(id=instance.id)
    except:
        old_instance = None

    if old_instance:
        if not old_instance.role == instance.role or not old_instance.organization == instance.organization:
            # get user
            user = instance.user
            
            # get instance permissions
            permissions = instance.role.permissions.select_related('content_type').all()
            user_permission_ids = list(Permission.objects.select_related('content_type').filter(group__user=user).values_list('id', flat=True))
            perms_to_add = permissions.exclude(id__in=user_permission_ids)

            # aggregate all current authorized organizations
            orgs = list(UserOrgRole.objects.select_related('user', 'organization', 'role').filter(user=user).values_list('organization__id', flat=True))

            # aggregate all updated unauthorized organizations
            unauthorized_orgs = list(Organization.objects.exclude(pk__in=orgs).values_list('id', flat=True))

            # filter through all old/unused object permissions and delete them
            filters = Q(content_type=ContentType.objects.get_for_model(Organization),
                object_pk__in=unauthorized_orgs, user=user)
            oldPerms = UserObjectPermission.objects.filter(filters)
            # print('oldPerms are: ', oldPerms)
            oldPerms.delete()

            # add all appropriate roles to user
            user.groups.add(instance.role)

            if instance.organization:
                organization_reports = MonthlyReport.objects.filter(organization=instance.organization)
                organization_articles = ContentArticle.objects.filter(client=instance.organization)

                # assign report permissions
                assign_perm('view_monthlyreport', instance.user, organization_reports)

                # assign content article permissions
                assign_perm('view_contentarticle', instance.user, organization_articles)


            for perm in perms_to_add:
                try:
                    with transaction.atomic():
                        assign_perm(perm.codename, instance.user, instance.organization)
                except:
                    pass

@receiver(post_save, sender=User)
def peform_user_deactivation_cleanup(sender, created, instance, **kwargs):
    if instance.is_active == False:
        perform_user_offboarding_tasks.delay(user_id=instance.id)