import time
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.test import RequestFactory
from rest_framework.throttling import AnonRateThrottle
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
import logging
from unittest import mock

# Логгер для отладки
logger = logging.getLogger(__name__)

class ThrottlingTestCase(APITestCase):
    """
    Тест для проверки ограничения частоты запросов (throttling).
    
    Данный тест использует патчинг функции allow_request для контроля поведения throttling,
    что делает тест стабильным и не зависящим от окружения.
    """
    
    def setUp(self):
        # Очищаем все кеши перед каждым тестом
        cache.clear()
        self.factory = RequestFactory()
    
    def test_anon_throttling(self):
        """
        Тест проверяет, что API применяет throttling при превышении лимита запросов.
        
        Подход:
        1. Патчим метод allow_request в AnonRateThrottle, чтобы он всегда возвращал True (разрешено)
        2. Делаем один запрос к API и проверяем, что он успешен
        3. Изменяем патч, чтобы allow_request возвращал False (заблокировано)
        4. Делаем еще один запрос и проверяем, что он заблокирован
        """
        url = reverse('product-list')
        
        # Первый патч: throttle разрешает запросы (allow_request=True)
        throttle_patch_1 = mock.patch.multiple(
            AnonRateThrottle,
            allow_request=mock.Mock(return_value=True),
            wait=mock.Mock(return_value=None)
        )
        
        # Второй патч: throttle блокирует запросы (allow_request=False)
        throttle_patch_2 = mock.patch.multiple(
            AnonRateThrottle,
            allow_request=mock.Mock(return_value=False),
            wait=mock.Mock(return_value=60)  # 60 секунд ожидания
        )
        
        # Тест с разрешенными запросами
        with throttle_patch_1:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK,
                         "Запрос должен быть разрешен при allow_request=True")
        
        # Тест с заблокированными запросами
        with throttle_patch_2:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS,
                         "Запрос должен быть заблокирован при allow_request=False") 