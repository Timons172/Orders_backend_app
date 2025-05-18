import time
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.cache import caches
import logging

# Логгер для отладки
logger = logging.getLogger(__name__)

class ThrottlingTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Очищаем все кеши перед запуском тестов
        for cache_name in caches:
            try:
                caches[cache_name].clear()
            except Exception as e:
                logger.warning(f"Could not clear cache '{cache_name}': {e}")

    def setUp(self):
        # Очищаем throttle кеш перед каждым тестом
        throttle_cache = caches['throttle']
        throttle_cache.clear()
        
        # Небольшая задержка, чтобы гарантировать, что кеш обновится
        time.sleep(0.1)
        
    def test_anon_throttling(self):
        url = reverse('product-list')  # /api/products/
        
        # Маркер для проверки преждевременной блокировки
        premature_block = False
        
        # Совершаем 60 успешных GET-запросов
        for i in range(60):
            response = self.client.get(url)
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                premature_block = True
                self.fail(f"Запрос {i+1} заблокирован преждевременно")
        
        # Проверяем, что не было преждевременной блокировки
        self.assertFalse(premature_block, "Запрос был заблокирован до достижения лимита")
        
        # 61-й запрос должен быть заблокирован троттлингом
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS,
                     f"61-й запрос не был заблокирован") 