from django.contrib import admin
from .models import Organization, Address
from guardian.admin import GuardedModelAdmin

class OrganizationAdmin(GuardedModelAdmin):
    list_display = ('dba_name', 'slug', 'created_at')
    search_fields = ('dba_name', 'business_email')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


class AddressAdmin(GuardedModelAdmin):
    list_display = ('organization', 'name_for_directory', 'street_1', 'city', 'state', 'zipcode')
    search_fields = ('organization', 'street_1', 'name_for_directory')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

admin.site.register(Address, AddressAdmin)
admin.site.register(Organization, OrganizationAdmin )