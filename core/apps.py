from django.apps import AppConfig
from django.contrib.auth import get_user_model

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        User = get_user_model()
        username = 'admin'
        email = 'admin@example.com'
        password = 'admin123'

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            print(f"Superuser '{username}' created with password '{password}'")