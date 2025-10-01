from django.apps import AppConfig

class AuthappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authapp'

    def ready(self):
        # Import signals here if you add them later
        try:
            import authapp.signals  # noqa
        except ImportError:
            pass
