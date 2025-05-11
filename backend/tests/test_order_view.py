import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact
from unittest.mock import patch


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
def test_data(test_user):
    """Создание тестовых данных для заказа"""
    # Создаем магазин
    shop = Shop.objects.create(name='Test Shop')
    
    # Создаем категорию
    category = Category.objects.create(name='Test Category')
    
    # Создаем продукт
    product = Product.objects.create(
        name='Test Product',
        category=category
    )
    
    # Создаем информацию о продукте
    product_info = ProductInfo.objects.create(
        product=product,
        shop=shop,
        name='Test Product Info',
        quantity=10,
        price=100.00,
        price_rrc=120.00
    )
    
    # Создаем контакт для доставки
    contact = Contact.objects.create(
        user=test_user['user'],
        type='address',
        value='Test Address'
    )
    
    # Создаем заказ и добавляем в него товар
    order = Order.objects.create(
        user=test_user['user'],
        status='new'
    )
    
    order_item = OrderItem.objects.create(
        order=order,
        product=product,
        shop=shop,
        quantity=2
    )
    
    # Создаем уже подтвержденный заказ для тестирования списка заказов
    confirmed_order = Order.objects.create(
        user=test_user['user'],
        status='confirmed',
        contact=contact
    )
    
    OrderItem.objects.create(
        order=confirmed_order,
        product=product,
        shop=shop,
        quantity=1
    )
    
    return {
        'shop': shop,
        'category': category,
        'product': product,
        'contact': contact,
        'order': order,
        'confirmed_order': confirmed_order
    }


@pytest.mark.django_db
class TestOrderViewSet:
    def test_list_orders(self, api_client, test_user, test_data):
        """Тест получения списка заказов"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('order-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 1  # Только подтвержденные заказы
        assert response.data['results'][0]['status'] == 'confirmed'
    
    def test_retrieve_order(self, api_client, test_user, test_data):
        """Тест получения конкретного заказа"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('order-detail', args=[test_data['confirmed_order'].id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == test_data['confirmed_order'].id
        assert response.data['status'] == 'confirmed'
    
    def test_confirm_order(self, api_client, test_user, test_data):
        """Тест подтверждения заказа"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        # Mock функцию отправки email
        with patch('backend.tasks.send_order_confirmation_email.delay') as mock_send:
            url = reverse('order-list')
            data = {
                'contact_id': test_data['contact'].id
            }
            
            response = api_client.post(url, data)
            
            assert response.status_code == status.HTTP_201_CREATED
            assert response.data['status'] == 'confirmed'
            
            # Проверяем, что заказ был обновлен в базе данных
            order = Order.objects.get(id=test_data['order'].id)
            assert order.status == 'confirmed'
            assert order.contact.id == test_data['contact'].id
            
            # Проверяем, что задача отправки email была вызвана
            mock_send.assert_called_once()
    
    def test_confirm_order_no_items(self, api_client, test_user):
        """Тест подтверждения пустого заказа"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        # Создаем пустую корзину
        Order.objects.create(user=test_user['user'], status='new')
        
        # Создаем контакт для доставки
        contact = Contact.objects.create(
            user=test_user['user'],
            type='address',
            value='Test Address'
        )
        
        url = reverse('order-list')
        data = {
            'contact_id': contact.id
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_confirm_order_invalid_contact(self, api_client, test_user, test_data):
        """Тест подтверждения заказа с некорректным контактом"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('order-list')
        data = {
            'contact_id': 999  # Несуществующий ID
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
    
    def test_authentication_required(self, api_client):
        """Тест доступа без аутентификации"""
        url = reverse('order-list')
        
        # GET запрос
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # POST запрос
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 