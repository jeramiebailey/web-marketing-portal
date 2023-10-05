from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from guardian.admin import GuardedModelAdmin
from .models import *

class WebsiteBuildAdmin(GuardedModelAdmin, SimpleHistoryAdmin):
    list_display = ["organization", "is_active", "date_created"]

admin.site.register(WebsiteBuild, WebsiteBuildAdmin)