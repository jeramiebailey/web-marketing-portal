from checklists.models import Checklist, ChecklistItem
from .models import WebsiteBuild
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm
from django.db import transaction
from guardian.models import UserObjectPermission
from datetime import datetime
from datetime import timedelta
from django.db.models import F


@receiver(pre_save, sender=WebsiteBuild)
def update_checklist_item_dates(sender, instance, **kwargs):
        try:
            previous_instance = WebsiteBuild.objects.get(id=instance.id)
        except:
            previous_instance = None

        try:
            old_date = previous_instance.start_date
            new_date = instance.start_date
        except:
            old_date = None
            new_date = None
        
        if previous_instance and old_date != new_date:
            delta = new_date - old_date
            build_checklist_items = instance.build_checklist.checklist_items
            deploy_checklist_items = instance.deploy_checklist.checklist_items
            build_checklist_items.update(due=F('due') + timedelta(delta.days))
            deploy_checklist_items.update(due=F('due') + timedelta(delta.days))




# @receiver(post_save, sender=ChecklistTemplateItemAttachment)
# def assign_checklist_template_item_attachment_perms(sender, instance, created, **kwargs):
#     if created:
#         assign_perm('view_checklisttemplateitemattachment', instance.created_by, instance)
#         assign_perm('change_checklisttemplateitemattachment', instance.created_by, instance)
#         assign_perm('delete_checklisttemplateitemattachment', instance.created_by, instance)


# @receiver(post_save, sender=ChecklistItem)
# def assign_checklist_item_perms(sender, instance, created, **kwargs):
#     if created:
#         assign_perm('view_checklistitem', instance.created_by, instance)
#         assign_perm('change_checklistitem', instance.created_by, instance)
#         assign_perm('delete_checklistitem', instance.created_by, instance)

# @receiver(post_save, sender=ChecklistItemAttachment)
# def assign_checklist_template_item_attachment_perms(sender, instance, created, **kwargs):
#     if created:
#         assign_perm('view_checklistitemattachment', instance.created_by, instance)
#         assign_perm('change_checklistitemattachment', instance.created_by, instance)
#         assign_perm('delete_checklistitemattachment', instance.created_by, instance)