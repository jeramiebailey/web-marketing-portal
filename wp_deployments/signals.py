from .models import WebApp
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm
from django.db import transaction
from guardian.models import UserObjectPermission
from django.db.models import Q

@receiver(post_save, sender=WebApp)
def delete_after_clean(sender, instance, created, **kwargs):
    if not created and instance.scheduled_for_deletion == True:
        try:
            delete_app = instance.delete()
        except:
            pass