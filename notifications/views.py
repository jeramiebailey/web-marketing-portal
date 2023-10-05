from django.shortcuts import render
from rest_framework import mixins, status, viewsets, permissions
from notifications.models import SystemNotification
from notifications.serializers import SystemNotificationSerializer
from rest_framework.permissions import IsAuthenticated

class SystemNotificationViewSet(viewsets.ModelViewSet):
    queryset = SystemNotification.objects.filter(is_active=True)
    serializer_class = SystemNotificationSerializer
    permission_classes = (IsAuthenticated,)