from django.apps import AppConfig


class AccountHealthConfig(AppConfig):
    name = 'account_health'
    verbose_name = "Account Health"

    def ready(self):
        import account_health.signals
