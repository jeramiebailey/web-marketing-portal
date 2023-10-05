from django.apps import AppConfig


class ReportingConfig(AppConfig):
    name = 'reporting'
    verbose_name = 'reporting'

    def ready(self):
        try:
            import reporting.signals  # noqa F401
        except ImportError:
            pass