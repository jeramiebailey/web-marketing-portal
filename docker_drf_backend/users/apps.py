from django.apps import AppConfig


class UsersAppConfig(AppConfig):

    name = "docker_drf_backend.users"
    verbose_name = "Users"

    def ready(self):
        import docker_drf_backend.users.signals 
        # try:
        #     import docker_drf_backend.users.signals  # noqa F401
        # except ImportError:
        #     pass
