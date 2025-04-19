from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Shop(models.Model):
    """
    Модель магазина/поставщика товаров.
    Содержит название и ссылку на сайт поставщика.
    """
    name = models.CharField(max_length=100, verbose_name='Store name')
    url = models.URLField(verbose_name='Store URL', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Store'
        verbose_name_plural = 'Stores'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Модель категории товаров.
    Категория может относиться к нескольким магазинам через many-to-many связь.
    """
    shops = models.ManyToManyField(Shop, related_name='categories', verbose_name='Stores')
    name = models.CharField(max_length=100, verbose_name='Category name')
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Модель товара.
    Каждый товар принадлежит определенной категории.
    """
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, verbose_name='Category')
    name = models.CharField(max_length=250, verbose_name='Product name')
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """
    Модель информации о товаре в конкретном магазине.
    Содержит цены, количество и другую информацию о товаре у конкретного поставщика.
    Один и тот же товар может иметь разные цены и характеристики у разных поставщиков.
    """
    product = models.ForeignKey(Product, related_name='product_infos', on_delete=models.CASCADE, verbose_name='Product')
    shop = models.ForeignKey(Shop, related_name='product_infos', on_delete=models.CASCADE, verbose_name='Store')
    name = models.CharField(max_length=250, verbose_name='Product name')
    quantity = models.PositiveIntegerField(verbose_name='Quantity in stock')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Price')
    price_rrc = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Recommended retail price')
    
    class Meta:
        verbose_name = 'Product information'
        verbose_name_plural = 'Product information'
        constraints = [
            models.UniqueConstraint(fields=['product', 'shop'], name='unique_product_shop')
        ]
    
    def __str__(self):
        return f'{self.name} - {self.shop.name}'


class Parameter(models.Model):
    """
    Модель параметра/характеристики товара.
    Например: размер, цвет, материал и т.д.
    """
    name = models.CharField(max_length=100, verbose_name='Parameter name')
    
    class Meta:
        verbose_name = 'Parameter'
        verbose_name_plural = 'Parameters'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    """
    Модель значения параметра для конкретного товара у конкретного поставщика.
    Связывает товар с его параметрами и их значениями.
    """
    product_info = models.ForeignKey(ProductInfo, related_name='parameters', on_delete=models.CASCADE, verbose_name='Product information')
    parameter = models.ForeignKey(Parameter, related_name='product_parameters', on_delete=models.CASCADE, verbose_name='Parameter')
    value = models.CharField(max_length=100, verbose_name='Parameter value')
    
    class Meta:
        verbose_name = 'Product parameter'
        verbose_name_plural = 'Product parameters'
        constraints = [
            models.UniqueConstraint(fields=['product_info', 'parameter'], name='unique_product_parameter')
        ]
    
    def __str__(self):
        return f'{self.parameter.name}: {self.value}'


class Order(models.Model):
    """
    Модель заказа пользователя.
    Содержит информацию о статусе и дате создания заказа.
    Товары в заказе хранятся в связанной модели OrderItem.
    """
    STATUS_CHOICES = (
        ('new', 'New'),  # Новый заказ (корзина)
        ('confirmed', 'Confirmed'),  # Заказ подтвержден
        ('assembled', 'Assembled'),  # Заказ собран
        ('sent', 'Sent'),  # Заказ отправлен
        ('delivered', 'Delivered'),  # Заказ доставлен
        ('canceled', 'Canceled'),  # Заказ отменен
    )
    
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE, verbose_name='User')
    dt = models.DateTimeField(auto_now_add=True, verbose_name='Order date')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='new', verbose_name='Order status')
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-dt']
    
    def __str__(self):
        return f'Order {self.id} from {self.dt.strftime("%Y-%m-%d %H:%M")}'


class OrderItem(models.Model):
    """
    Модель элемента заказа.
    Связывает заказ с товарами, их количеством и магазином-поставщиком.
    """
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name='Order')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Product')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, verbose_name='Store')
    quantity = models.PositiveIntegerField(verbose_name='Quantity')
    
    class Meta:
        verbose_name = 'Order item'
        verbose_name_plural = 'Order items'
    
    def __str__(self):
        return f'{self.product.name} - {self.quantity} pcs'


class Contact(models.Model):
    """
    Модель контактной информации пользователя.
    Может хранить адреса доставки или телефоны.
    """
    TYPE_CHOICES = (
        ('phone', 'Phone'),  # Телефон пользователя
        ('address', 'Address'),  # Адрес доставки
    )
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Contact type')
    user = models.ForeignKey(User, related_name='contacts', on_delete=models.CASCADE, verbose_name='User')
    value = models.TextField(verbose_name='Contact value')
    
    class Meta:
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
    
    def __str__(self):
        return f'{self.type}: {self.value}'
