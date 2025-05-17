from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class ThrottlingTestCase(APITestCase):
    def test_anon_throttling(self):
        url = reverse('user-register')
        data = {
            "username": "userthrottle",
            "email": "userthrottle@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password": "password123",
            "password_repeat": "password123"
        }
        for _ in range(3):
            response = self.client.post(url, data)
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS) 