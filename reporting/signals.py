from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm
from django.db import transaction
from .models import MonthlyReport
from docker_drf_backend.users.models import UserOrgRole

# @receiver(pre_save, sender=MonthlyReport)
# def handle_report_perms(sender, instance, **kwargs):
#         try:
#             previous_instance = MonthlyReport.objects.get(id=instance.id)
#         except:
#             previous_instance = None

#         try:
#             old_creator = previous_instance.creator
#             new_creator = instance.creator
#         except:
#             old_creator = None
#             new_creator = None
        
#         if previous_instance and old_creator != new_creator:
#             assign_perm('view_monthlyreport', instance.old_creator, instance)

@receiver(post_save, sender=MonthlyReport)
def handle_post_report_create(sender, instance, created, **kwargs):
    if created and instance.organization:
        # handle roles and permissions
        org = instance.organization
        org_roles = org.user_roles.prefetch_related('organization', 'user', 'role').all()

        if org_roles.first():
            for role in org_roles:
                assign_perm('view_monthlyreport', role.user, instance)
                assign_perm('change_monthlyreport', role.user, instance)

        # handle report presentation creation
        if not instance.presentation:
            instance.create_monthly_report_presentation()


# @receiver(post_save, sender=MonthlyReport)
# def handle_presentation_create(sender, instance, created, **kwargs):
#     print('handle_presentation_create fired')
#     if created and instance.organization:
#         if not instance.presentation:
#             instance.create_monthly_report_presentation()
#             print('handle_post_report_create: should have created report here')