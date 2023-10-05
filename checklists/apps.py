from django.apps import AppConfig


class ChecklistsConfig(AppConfig):
    name = 'checklists'
    verbose_name = "Checklists"

    def ready(self):
        try:
            import checklists.signals  # noqa F401
        except ImportError:
            pass