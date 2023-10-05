from django.apps import AppConfig


class WpDeploymentsConfig(AppConfig):
    name = 'wp_deployments'
    verbose_name = 'WP Deployments'

    def ready(self):
        try:
            import wp_deployments.signals  # noqa F401
        except ImportError:
            pass