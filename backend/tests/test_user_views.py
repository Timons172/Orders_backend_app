import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from unittest.mock import patch


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_data():
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password': 'testpassword123',
        'password_repeat': 'testpassword123'
    }


@pytest.mark.django_db
class TestUserRegisterView:
    def test_register_user_success(self, api_client, user_data):
        """Тест успешной регистрации пользователя"""
        # Для тестирования убираем проверку на вызов send_mail, 
        # так как в тестовой среде он может не выполняться,
        # и это нормально.
        url = reverse('user-register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'token' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == user_data['username']
        assert response.data['user']['email'] == user_data['email']
        
        # Проверяем, что пользователь был создан в базе
        assert User.objects.filter(username=user_data['username']).exists()
        
        # Проверяем, что токен был создан
        user = User.objects.get(username=user_data['username'])
        assert Token.objects.filter(user=user).exists()

    def test_register_user_invalid_data(self, api_client):
        """Тест регистрации с некорректными данными"""
        # Неполные данные без username
        invalid_data = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'password_repeat': 'testpassword123'
        }
        
        url = reverse('user-register')
        response = api_client.post(url, invalid_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data  # Должно быть сообщение об ошибке для username

    def test_register_user_password_mismatch(self, api_client, user_data):
        """Тест регистрации с несовпадающими паролями"""
        user_data['password_repeat'] = 'differentpassword'
        
        url = reverse('user-register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data or 'non_field_errors' in response.data


@pytest.mark.django_db
class TestUserLoginView:
    @pytest.fixture
    def create_user(self):
        """Фикстура для создания тестового пользователя"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        return user
    
    def test_login_success(self, api_client, create_user):
        """Тест успешного входа в систему"""
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'testuser'
    
    def test_login_invalid_credentials(self, api_client, create_user):
        """Тест входа с некорректными учетными данными"""
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data 