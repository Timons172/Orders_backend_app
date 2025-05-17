import time
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class ThrottlingTestCase(APITestCase):
    def test_anon_throttling(self):
        time.sleep(61)  # Ждём чуть больше минуты, чтобы лимит сбросился
        url = reverse('product-list')  # /api/products/
        # Совершаем 60 успешных GET-запросов
        for i in range(60):
            response = self.client.get(url)
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        # 61-й запрос должен быть заблокирован троттлингом
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS) 