import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from backend.models import Contact


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user():
    """Создание тестового пользователя"""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123'
    )
    # Создаем токен для аутентификации
    token = Token.objects.create(user=user)
    return {
        'user': user,
        'token': token.key
    }


@pytest.fixture
def another_user():
    """Создание другого тестового пользователя"""
    user = User.objects.create_user(
        username='anotheruser',
        email='another@example.com',
        password='testpassword123'
    )
    # Создаем токен для аутентификации
    token = Token.objects.create(user=user)
    return {
        'user': user,
        'token': token.key
    }


@pytest.fixture
def test_contacts(test_user, another_user):
    """Создание тестовых контактов"""
    # Создаем контакты для тестового пользователя
    contact1 = Contact.objects.create(
        user=test_user['user'],
        type='phone',
        value='+1234567890'
    )
    
    contact2 = Contact.objects.create(
        user=test_user['user'],
        type='address',
        value='Test Address'
    )
    
    # Создаем контакт для другого пользователя
    other_contact = Contact.objects.create(
        user=another_user['user'],
        type='email',
        value='other@example.com'
    )
    
    return {
        'own_contacts': [contact1, contact2],
        'other_contact': other_contact
    }


@pytest.mark.django_db
class TestContactViewSet:
    def test_list_contacts(self, api_client, test_user, test_contacts):
        """Тест получения списка контактов"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('contact-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 2  # Только свои контакты
        
        # Проверяем, что возвращены только контакты тестового пользователя
        contact_ids = [item['id'] for item in response.data['results']]
        expected_ids = [contact.id for contact in test_contacts['own_contacts']]
        assert set(contact_ids) == set(expected_ids)
    
    def test_create_contact(self, api_client, test_user):
        """Тест создания контакта"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('contact-list')
        data = {
            'type': 'address',  # Используем валидный тип контакта из модели (phone или address)
            'value': 'New Test Address'
        }
        
        response = api_client.post(url, data)
        
        # Печатаем ответ для отладки
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['type'] == data['type']
        assert response.data['value'] == data['value']
        
        # Проверяем, что контакт был создан в базе данных
        assert Contact.objects.filter(value=data['value']).exists()
        
        # Проверяем, что контакт принадлежит правильному пользователю
        contact = Contact.objects.get(value=data['value'])
        assert contact.user.id == test_user['user'].id
    
    def test_retrieve_contact(self, api_client, test_user, test_contacts):
        """Тест получения конкретного контакта"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('contact-detail', args=[test_contacts['own_contacts'][0].id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == test_contacts['own_contacts'][0].id
        assert response.data['type'] == test_contacts['own_contacts'][0].type
        assert response.data['value'] == test_contacts['own_contacts'][0].value
    
    def test_update_contact(self, api_client, test_user, test_contacts):
        """Тест обновления контакта"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('contact-detail', args=[test_contacts['own_contacts'][0].id])
        data = {
            'type': 'phone',
            'value': '+9876543210'  # Новый номер телефона
        }
        
        response = api_client.put(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['value'] == data['value']
        
        # Проверяем, что контакт был обновлен в базе данных
        contact = Contact.objects.get(id=test_contacts['own_contacts'][0].id)
        assert contact.value == data['value']
    
    def test_delete_contact(self, api_client, test_user, test_contacts):
        """Тест удаления контакта"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('contact-detail', args=[test_contacts['own_contacts'][0].id])
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Проверяем, что контакт был удален из базы данных
        assert not Contact.objects.filter(id=test_contacts['own_contacts'][0].id).exists()
    
    def test_cannot_access_other_users_contact(self, api_client, test_user, test_contacts):
        """Тест невозможности доступа к контактам другого пользователя"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('contact-detail', args=[test_contacts['other_contact'].id])
        response = api_client.get(url)
        
        # Должен вернуть 404, т.к. get_queryset фильтрует только контакты текущего пользователя
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_authentication_required(self, api_client, test_contacts):
        """Тест доступа без аутентификации"""
        # Без токена аутентификации
        url = reverse('contact-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        url = reverse('contact-detail', args=[test_contacts['own_contacts'][0].id])
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 