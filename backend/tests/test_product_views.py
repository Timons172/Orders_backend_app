import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from backend.models import Shop, Category, Product, ProductInfo


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_test_data():
    """Создание тестовых данных для продуктов"""
    # Создаем магазин
    shop = Shop.objects.create(name='Test Shop')
    
    # Создаем категорию
    category = Category.objects.create(name='Test Category')
    
    # Создаем продукты
    products = []
    for i in range(3):
        product = Product.objects.create(
            name=f'Test Product {i}',
            category=category
        )
        products.append(product)
        
        # Создаем информацию о продукте
        ProductInfo.objects.create(
            product=product,
            shop=shop,
            name=f'Test Product Info {i}',
            quantity=10,
            price=100.00,
            price_rrc=120.00
        )
    
    return {
        'shop': shop,
        'category': category,
        'products': products
    }


@pytest.mark.django_db
class TestProductViewSet:
    def test_list_products(self, api_client, create_test_data):
        """Тест получения списка продуктов"""
        url = reverse('product-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 3
    
    def test_retrieve_product(self, api_client, create_test_data):
        """Тест получения конкретного продукта"""
        product_id = create_test_data['products'][0].id
        url = reverse('product-detail', args=[product_id])
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == product_id
        assert response.data['name'] == 'Test Product 0'


@pytest.mark.django_db
class TestProductInfoViewSet:
    def test_list_product_info(self, api_client, create_test_data):
        """Тест получения списка информации о продуктах"""
        url = '/api/product-info/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 3
    
    def test_filter_by_shop(self, api_client, create_test_data):
        """Тест фильтрации по магазину"""
        shop_id = create_test_data['shop'].id
        url = f"/api/product-info/?shop={shop_id}"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 3
        
        # Проверяем что все продукты из нужного магазина
        for item in response.data['results']:
            assert item['shop']['id'] == shop_id
    
    def test_filter_by_category(self, api_client, create_test_data):
        """Тест фильтрации по категории"""
        category_id = create_test_data['category'].id
        url = f"/api/product-info/?category={category_id}"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 3
        
        # Проверяем что все продукты из нужной категории
        for item in response.data['results']:
            assert item['product']['category']['id'] == category_id
    
    def test_search_by_name(self, api_client, create_test_data):
        """Тест поиска по названию"""
        search_term = 'Product Info 1'
        url = f"/api/product-info/?search={search_term}"
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        
        # Проверяем, что в результатах есть хотя бы один товар с нужным названием
        assert len(response.data['results']) > 0
        
        # Проверяем что в результате только те продукты, которые содержат строку поиска
        for item in response.data['results']:
            assert 'Test Product Info 1' == item['name'] 