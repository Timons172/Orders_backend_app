import time
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.test import RequestFactory
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.cache import cache
from django.contrib.auth.models import AnonymousUser
import logging

# Логгер для отладки
logger = logging.getLogger(__name__)

# Создаем специальный класс для тестирования
class TestThrottle(AnonRateThrottle):
    rate = '3/minute'
    
    # Переопределяем метод получения ключа кеша для стабильности
    def get_ident(self, request):
        return 'test-ident'

class ThrottlingTestCase(APITestCase):
    def setUp(self):
        # Очищаем все кеши перед каждым тестом
        cache.clear()
        self.factory = RequestFactory()
    
    def test_anon_throttling(self):
        """
        Тест проверяет работу ограничения частоты запросов для анонимных пользователей.
        
        В этом тесте мы тестируем непосредственно класс TestThrottle с фиксированным идентификатором.
        """
        # Создаем тестовый объект ограничителя
        throttle = TestThrottle()
        
        # Создаем тестовый запрос с анонимным пользователем и всеми необходимыми атрибутами
        request = self.factory.get('/')
        request.user = AnonymousUser()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Тестируем первые 3 запроса - они должны быть разрешены
        for i in range(3):
            allowed = throttle.allow_request(request, None)
            self.assertTrue(allowed, f"Запрос {i+1} должен быть разрешен")
            logger.debug(f"Запрос {i+1}: разрешен = {allowed}")
        
        # Четвертый запрос должен быть заблокирован
        allowed = throttle.allow_request(request, None)
        self.assertFalse(allowed, "Четвертый запрос должен быть заблокирован")
        logger.debug(f"Запрос 4: разрешен = {allowed}") 