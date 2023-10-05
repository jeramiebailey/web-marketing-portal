from django.apps import AppConfig


class ClientOnboardingConfig(AppConfig):
    name = 'client_onboarding'
    verbose_name = "Client Onboarding"
    
    def ready(self):
        try:
            import client_onboarding.signals  # noqa F401
        except ImportError:
            pass