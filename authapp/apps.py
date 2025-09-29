from django.apps import AppConfig
from django.contrib.auth import get_user_model
import os

class AuthappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authapp'

    def ready(self):
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email=os.environ.get("ADMIN_EMAIL", "admin@example.com"),
                password=os.environ.get("ADMIN_PASSWORD", "admin123")
            )
