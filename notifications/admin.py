from django.contrib import admin
from .models import Notification, SystemNotification
from guardian.admin import GuardedModelAdmin

class NotificationAdmin(GuardedModelAdmin):
    list_display = ('text', 'owner', 'created_at')
    search_fields = ('text', 'owner')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

admin.site.register(Notification, NotificationAdmin )

class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'live_date', 'end_date', 'created_at', 'is_active',)
    ordering = ('-created_at',)

admin.site.register(SystemNotification, SystemNotificationAdmin)