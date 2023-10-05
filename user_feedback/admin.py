from django.contrib import admin
from guardian.admin import GuardedModelAdmin
from .models import *

class UserFeedbackAdmin(GuardedModelAdmin):
    pass

admin.site.register(UserFeedback, UserFeedbackAdmin)