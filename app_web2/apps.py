from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class AppWeb2Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_web2'

    def ready(self):
        autodiscover_modules('stark')
