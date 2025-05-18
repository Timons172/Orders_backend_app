import time
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.test import RequestFactory
from rest_framework.throttling import AnonRateThrottle
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
import logging

# Логгер для отладки
logger = logging.getLogger(__name__)

class ThrottlingTestCase(APITestCase):
    def setUp(self):
        # Очищаем все кеши перед каждым тестом
        cache.clear()
        self.factory = RequestFactory()
    
    def test_anon_throttling(self):
        """
        Тест проверяет, что API применяет throttling при превышении лимита запросов.
        
        Данный тест симулирует превышение лимита и проверяет, что сервер возвращает
        HTTP 429 Too Many Requests.
        """
        url = reverse('product-list')
        
        # Первая часть теста - "нормальная" проверка throttling
        # Выполняем 3 запроса, которые должны быть успешными
        for i in range(3):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK,
                          f"Запрос {i+1} должен быть успешным")
        
        # Вторая часть - "искусственная" имитация превышения лимита
        # Создаем искусственный "отпечаток" пользователя для throttling
        throttle = AnonRateThrottle()
        request = self.factory.get(url)
        request.user = AnonymousUser()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Получаем ключ кеша для текущего запроса
        cache_key = throttle.get_cache_key(request, None)
        
        if not cache_key:
            self.fail("Не удалось получить ключ кеша для throttling")
        
        # Записываем в кеш историю из 61 запроса за последнюю минуту
        # что превышает лимит в 60 запросов и должно вызвать блокировку
        now = time.time()
        history = [now - i for i in range(61)]  # список штампов времени 61 запроса
        
        # Сохраняем историю запросов в кеш
        cache.set(cache_key, history, 60)
        
        # Система должна увидеть подмененную историю запросов и заблокировать новый запрос
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS,
                      "После превышения лимита запрос должен быть заблокирован") 