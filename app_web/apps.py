from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class AppWebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_web'
