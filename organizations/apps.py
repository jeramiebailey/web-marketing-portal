from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    name = 'organizations'
    verbose_name = "Organizations"

    def ready(self):
        import organizations.signals 
        # try:
        #     import organizations.signals  # noqa F401
        # except ImportError:
        #     pass