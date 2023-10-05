from django.contrib import admin
from .models import MonthlyReport, ReportEmailEntry
from guardian.admin import GuardedModelAdmin
from import_export.fields import Field
from simple_history.admin import SimpleHistoryAdmin

class MonthlyReportAdmin(GuardedModelAdmin):
    list_display = ["organization", "month", "status", "date_created"]

admin.site.register(MonthlyReport, MonthlyReportAdmin)

class ReportEmailEntryAdmin(admin.ModelAdmin):
    list_display = ('email', 'link_clicked', 'uuid', 'date_sent',)
    search_fields = ('email', 'uuid', 'date_sent')
    ordering = ('-date_sent',)


admin.site.register(ReportEmailEntry, ReportEmailEntryAdmin)