import yaml
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter

class Command(BaseCommand):
    """
    Команда Django для импорта товаров из YAML файлов.
    
    Данная команда позволяет загружать товары из файлов YAML формата
    в базу данных системы. Файл должен содержать информацию о магазине,
    категориях и товарах в определенной структуре.
    """
    help = 'Import products from YAML files'

    def add_arguments(self, parser):
        """
        Добавляет аргументы командной строки.
        """
        parser.add_argument('file_path', type=str, help='Path to the YAML file with products')

    def handle(self, *args, **options):
        """
        Основной метод команды, который вызывается при её выполнении.
        """
        file_path = options['file_path']
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File {file_path} does not exist'))
            return
        
        # Загружаем данные из YAML файла
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = yaml.safe_load(file)
            except yaml.YAMLError as e:
                self.stdout.write(self.style.ERROR(f'Error parsing YAML file: {e}'))
                return
        
        self.stdout.write(self.style.SUCCESS(f'Successfully loaded YAML file: {file_path}'))
        
        # Импортируем товары из загруженных данных
        try:
            self.import_products(data)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing products: {e}'))
            return
            
        self.stdout.write(self.style.SUCCESS('Products import completed successfully'))
    
    @transaction.atomic
    def import_products(self, data):
        """
        Импортирует товары из данных YAML в базу данных.
        Использует атомарную транзакцию для обеспечения целостности данных.
        """
        # Создаем или получаем магазин
        shop_name = data.get('shop')
        shop, created = Shop.objects.get_or_create(name=shop_name)
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new shop: {shop_name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing shop: {shop_name}'))
        
        # Обрабатываем категории товаров
        categories = data.get('categories', [])
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name']
            )
            
            # Добавляем магазин в список магазинов категории
            category.shops.add(shop)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created new category: {category.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Using existing category: {category.name}'))
        
        # Обрабатываем товары
        goods = data.get('goods', [])
        for product_data in goods:
            # Находим категорию для данного товара
            category_id = product_data['category']
            category = next((c for c in categories if c['id'] == category_id), None)
            
            if not category:
                self.stdout.write(self.style.WARNING(f'Category ID {category_id} not found, skipping product {product_data["name"]}'))
                continue
            
            category_obj = Category.objects.get(name=category['name'])
            
            # Создаем или получаем товар
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                category=category_obj
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created new product: {product.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Using existing product: {product.name}'))
            
            # Создаем или обновляем информацию о товаре для конкретного магазина
            product_info, created = ProductInfo.objects.update_or_create(
                product=product,
                shop=shop,
                defaults={
                    'name': product_data['name'],
                    'quantity': product_data['quantity'],
                    'price': product_data['price'],
                    'price_rrc': product_data['price_rrc']
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created product info for {product.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Updated product info for {product.name}'))
            
            # Обрабатываем параметры товара
            parameters = product_data.get('parameters', {})
            for param_name, param_value in parameters.items():
                parameter, created = Parameter.objects.get_or_create(name=param_name)
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created new parameter: {param_name}'))
                
                # Создаем или обновляем значение параметра для товара
                product_param, created = ProductParameter.objects.update_or_create(
                    product_info=product_info,
                    parameter=parameter,
                    defaults={'value': str(param_value)}
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Added parameter {param_name}={param_value} to {product.name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Updated parameter {param_name}={param_value} for {product.name}')) 