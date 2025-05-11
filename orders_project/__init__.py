# Импорт и инициализация Celery при загрузке Django-приложения
from .celery import app as celery_app

__all__ = ['celery_app']
