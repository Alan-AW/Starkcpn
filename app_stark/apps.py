from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class AppStarkConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_stark'
