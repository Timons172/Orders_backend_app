import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem


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
    """Создание тестовых данных для корзины"""
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
    
    return {
        'shop': shop,
        'category': category,
        'product': product,
        'product_info': product_info
    }


@pytest.mark.django_db
class TestCartView:
    def test_get_empty_cart(self, api_client, test_user):
        """Тест получения пустой корзины"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('cart')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'new'
        assert len(response.data['items']) == 0
    
    def test_add_item_to_cart(self, api_client, test_user, test_data):
        """Тест добавления товара в корзину"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('cart')
        data = {
            'product': test_data['product'].id,
            'shop': test_data['shop'].id,
            'quantity': 2
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['items']) == 1
        assert response.data['items'][0]['product']['id'] == test_data['product'].id
        assert response.data['items'][0]['quantity'] == 2
        
        # Проверяем, что товар был добавлен в базу данных
        order = Order.objects.get(user=test_user['user'], status='new')
        assert order.items.count() == 1
    
    def test_add_item_that_doesnt_exist(self, api_client, test_user):
        """Тест добавления несуществующего товара"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        url = reverse('cart')
        data = {
            'product': 999,  # Несуществующий ID
            'shop': 999,     # Несуществующий ID
            'quantity': 1
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Проверяем наличие ошибок валидации для полей product и shop
        assert 'product' in response.data or 'shop' in response.data or 'error' in response.data
    
    def test_delete_item_from_cart(self, api_client, test_user, test_data):
        """Тест удаления товара из корзины"""
        # Аутентифицируем клиент
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {test_user["token"]}')
        
        # Сначала добавляем товар в корзину
        cart = Order.objects.create(user=test_user['user'], status='new')
        item = OrderItem.objects.create(
            order=cart,
            product=test_data['product'],
            shop=test_data['shop'],
            quantity=1
        )
        
        url = reverse('cart')
        data = {
            'item_id': item.id
        }
        
        response = api_client.delete(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['items']) == 0
        
        # Проверяем, что товар был удален из базы данных
        assert not OrderItem.objects.filter(id=item.id).exists()
    
    def test_authentication_required(self, api_client):
        """Тест доступа без аутентификации"""
        url = reverse('cart')
        
        # GET запрос
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # POST запрос
        response = api_client.post(url, {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # DELETE запрос
        response = api_client.delete(url, {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED 