from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from account_health.models import AccountHealth
from account_health.tasks import pull_account_health_analytics, pull_all_account_data

@receiver(post_save, sender=AccountHealth)
def handle_post_account_health_create(sender, instance, created, **kwargs):
    if created and instance.account:
        # handle permissions
        instance.assign_account_health_permissions()

        # pull data
        pull_all_account_data.delay(object_id=instance.id)