from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.postgres.fields import JSONField, ArrayField


class UIComponent(models.Model):
    name = models.CharField(_("Component Name"), max_length=255, unique=True)
    verbose_name = models.CharField(_("Component Verbose Name"), max_length=255, null=True)
    attribute_fields = JSONField(null=True, blank=True)
    is_allowed = models.BooleanField(blank=True, default=True)

    def get_api_view_name(self):
        api_view_name = 'ui_components'
        return api_view_name

    class Meta:
        verbose_name = 'UI Component'
        verbose_name_plural = 'UI Components'
        permissions = (
            ('view_uicomponent__dep', 'View UI Component Deprecated'),
        )

    def __str__(self):
        return self.name