from django.db import models
from docker_drf_backend.users.models import User
from .constants import SEVERITY_LEVEL


class Notification(models.Model):
    text = models.CharField(max_length=255)
    owner = models.ForeignKey(User, related_name="notifications",
                              on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        permissions = (
            ('view_notification__dep', 'Cay  Andn view notification Deprecated'),
        )

    def __str__(self):
        return self.text

class SystemNotification(models.Model):
    message = models.TextField(max_length=500)
    live_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(blank=True, default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Notification"
        verbose_name_plural = "System Notifications"
        permissions = (
            ('view_systemnotification__dep', 'Can view system notification Deprecated'),
        )

    def __str__(self):
        return str(self.id)