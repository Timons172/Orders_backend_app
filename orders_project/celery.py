import os
from celery import Celery
from celery.schedules import crontab

# Установка переменной окружения, указывающей на файл настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orders_project.settings')

# Создание экземпляра приложения Celery
app = Celery('orders_project')

# Загрузка настроек из settings.py через namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение и регистрация задач из файлов tasks.py во всех приложениях Django
app.autodiscover_tasks()

# Настройка периодических задач
app.conf.beat_schedule = {
    # Каждые 30 минут проверяем и обрабатываем новые заказы
    'process-new-orders-every-30-minutes': {
        'task': 'backend.tasks.process_new_orders',
        'schedule': crontab(minute='*/30'),
    },
    # Каждые 2 часа обновляем доступность товаров для всех магазинов
    'update-all-shops-availability': {
        'task': 'backend.tasks.update_all_shops_availability',
        'schedule': crontab(hour='*/2'),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 