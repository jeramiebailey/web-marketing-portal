from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from .models import UserOrgRole, Preferences

from docker_drf_backend.users.forms import UserChangeForm, UserCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (("User", {"fields": ("name", "default_role", "phone_number", "title", 'avatar')}),) + auth_admin.UserAdmin.fieldsets
    list_display = ["id", "username", "name", "is_superuser"]
    search_fields = ["name"]


class UserOrgRoleAdmin(admin.ModelAdmin):
    
    search_fields = ('user', 'organization')

admin.site.register(UserOrgRole, UserOrgRoleAdmin)
admin.site.register(Preferences)