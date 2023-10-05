from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from guardian.admin import GuardedModelAdmin
from .models import *

class ChecklistTemplateAdmin(GuardedModelAdmin, SimpleHistoryAdmin):
    list_display = ["name", "archived", "created_by", "date_created", "last_updated"]
    history_list_display = ["status"]

class ChecklistTemplateItemAdmin(GuardedModelAdmin, SimpleHistoryAdmin):
    list_display = ["checklist", "name", "order", "department",]

class ChecklistAdmin(GuardedModelAdmin, SimpleHistoryAdmin):
    list_display = ["name", "archived", "created_by", "date_created", "last_updated"]

class ChecklistItemAdmin(GuardedModelAdmin, SimpleHistoryAdmin):
    list_display = ["checklist", "name", "order", "department", "assignee", "due", "completed", "date_created"]
    history_list_display = ["completed"]

class MasterChecklistTemplateAdmin(GuardedModelAdmin, SimpleHistoryAdmin):
    pass


admin.site.register(ChecklistTemplate, ChecklistTemplateAdmin)
admin.site.register(ChecklistTemplateItem, ChecklistTemplateItemAdmin)
admin.site.register(Checklist, ChecklistAdmin)
admin.site.register(ChecklistItem, ChecklistItemAdmin)
admin.site.register(ChecklistTemplateItemAttachment)
admin.site.register(ChecklistItemAttachment)
admin.site.register(MasterChecklistTemplate, MasterChecklistTemplateAdmin)
