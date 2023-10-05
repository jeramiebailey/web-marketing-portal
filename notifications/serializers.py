from rest_framework import serializers
from notifications.models import SystemNotification

class SystemNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemNotification
        fields = ('__all__')