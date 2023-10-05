from .models import Checklist, ChecklistTemplateItemAttachment, ChecklistItem, ChecklistItemAttachment
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm
from django.db import transaction
from guardian.models import UserObjectPermission


# @receiver(post_save, sender=Checklist)
# def assign_checklist_perms(sender, instance, created, **kwargs):
#     if created:
#         assign_perm('view_checklist', instance.created_by, instance)
#         assign_perm('change_checklist', instance.created_by, instance)
#         assign_perm('delete_checklist', instance.created_by, instance)


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