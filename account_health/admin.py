from django.contrib import admin
from account_health.models import AccountHealth
from guardian.admin import GuardedModelAdmin


class AccountHealthAdmin(GuardedModelAdmin):
    list_display = ('id', 'account', 'updated_at',)
    search_fields = ('account__dba_name',)
    ordering = ('account__dba_name',)


admin.site.register(AccountHealth, AccountHealthAdmin)