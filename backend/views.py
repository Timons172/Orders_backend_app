from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings

from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact
from .serializers import (
    ShopSerializer, CategorySerializer, ProductSerializer, ProductInfoSerializer,
    OrderSerializer, OrderItemSerializer, OrderItemCreateSerializer, ContactSerializer,
    UserSerializer, UserRegisterSerializer
)


class UserRegisterView(APIView):
    """
    API эндпоинт для регистрации новых пользователей.
    
    Принимает данные:
    - username - логин пользователя
    - email - электронная почта
    - first_name - имя
    - last_name - фамилия
    - password - пароль
    - password_repeat - повторение пароля
    
    Возвращает токен аутентификации и данные пользователя.
    Отправляет подтверждающее письмо на email пользователя.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # Создаем сериализатор для валидации данных регистрации
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            # Создаем нового пользователя
            user = serializer.save()
            # Генерируем токен аутентификации
            token, created = Token.objects.get_or_create(user=user)
            
            # Отправляем подтверждающее письмо
            subject = 'Registration confirmation'
            message = f'Thank you for registering on our platform, {user.first_name}!'
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [user.email]
            
            try:
                send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                print(f"Error sending email: {e}")
            
            # Возвращаем токен и данные пользователя
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        # Если данные не прошли валидацию, возвращаем ошибки
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(ObtainAuthToken):
    """
    API эндпоинт для входа пользователей в систему.
    
    Принимает данные:
    - username - логин пользователя
    - password - пароль
    
    Возвращает токен аутентификации и данные пользователя.
    """
    def post(self, request, *args, **kwargs):
        # Получаем логин и пароль из запроса
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Аутентифицируем пользователя
        user = authenticate(username=username, password=password)
        
        if user:
            # Генерируем токен аутентификации
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            })
        
        # Если аутентификация не удалась, возвращаем ошибку
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API эндпоинт для просмотра списка товаров.
    
    Только для чтения, без возможности изменения.
    Доступен всем пользователям без аутентификации.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]


class ProductInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API эндпоинт для просмотра детальной информации о товарах с возможностью фильтрации.
    
    Поддерживает фильтрацию по:
    - shop - ID магазина
    - category - ID категории
    - search - поисковый запрос по названию товара
    
    Только для чтения, без возможности изменения.
    Доступен всем пользователям без аутентификации.
    """
    queryset = ProductInfo.objects.all()
    serializer_class = ProductInfoSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # Получаем базовый набор данных
        queryset = ProductInfo.objects.all()
        
        # Получаем параметры фильтрации из запроса
        shop_id = self.request.query_params.get('shop', None)
        category_id = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        
        # Применяем фильтр по магазину
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        
        # Применяем фильтр по категории
        if category_id:
            queryset = queryset.filter(product__category_id=category_id)
        
        # Применяем поиск по названию
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(product__name__icontains=search)
            )
        
        return queryset


class CartView(APIView):
    """
    API эндпоинт для управления корзиной пользователя.
    
    Методы:
    - GET: получить текущую корзину пользователя
    - POST: добавить товар в корзину
    - DELETE: удалить товар из корзины
    
    Требуется аутентификация.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Получить текущую корзину пользователя (заказ со статусом "new")"""
        # Получаем или создаем корзину пользователя
        cart, created = Order.objects.get_or_create(
            user=request.user,
            status='new'
        )
        
        # Сериализуем корзину и возвращаем данные
        serializer = OrderSerializer(cart)
        return Response(serializer.data)
    
    def post(self, request):
        """Добавить товар в корзину"""
        # Получаем или создаем корзину пользователя
        cart, created = Order.objects.get_or_create(
            user=request.user,
            status='new'
        )
        
        # Валидируем данные о добавляемом товаре
        serializer = OrderItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            shop = serializer.validated_data['shop']
            quantity = serializer.validated_data['quantity']
            
            # Проверяем, доступен ли товар в указанном магазине
            try:
                product_info = ProductInfo.objects.get(product=product, shop=shop)
            except ProductInfo.DoesNotExist:
                return Response(
                    {'error': 'Product not available in the specified shop'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверяем, достаточно ли товара на складе
            if product_info.quantity < quantity:
                return Response(
                    {'error': 'Not enough items in stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Проверяем, есть ли уже этот товар в корзине
            try:
                # Если товар уже есть, увеличиваем количество
                cart_item = OrderItem.objects.get(
                    order=cart,
                    product=product,
                    shop=shop
                )
                cart_item.quantity += quantity
                cart_item.save()
            except OrderItem.DoesNotExist:
                # Если товара еще нет, создаем новую позицию
                OrderItem.objects.create(
                    order=cart,
                    product=product,
                    shop=shop,
                    quantity=quantity
                )
            
            # Возвращаем обновленную корзину
            return Response(OrderSerializer(cart).data)
        
        # Если данные не прошли валидацию, возвращаем ошибки
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """Удалить товар из корзины"""
        # Получаем или создаем корзину пользователя
        cart, created = Order.objects.get_or_create(
            user=request.user,
            status='new'
        )
        
        # Получаем ID товара для удаления
        item_id = request.data.get('item_id')
        
        try:
            # Находим и удаляем товар из корзины
            item = OrderItem.objects.get(id=item_id, order=cart)
            item.delete()
            return Response(OrderSerializer(cart).data)
        except OrderItem.DoesNotExist:
            # Если товар не найден, возвращаем ошибку
            return Response(
                {'error': 'Item not found in cart'},
                status=status.HTTP_404_NOT_FOUND
            )


class ContactViewSet(viewsets.ModelViewSet):
    """
    API эндпоинт для управления контактами пользователя (адреса, телефоны).
    
    Поддерживает все CRUD операции:
    - GET: получить список контактов или детали конкретного контакта
    - POST: создать новый контакт
    - PUT/PATCH: обновить существующий контакт
    - DELETE: удалить контакт
    
    Требуется аутентификация.
    """
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Возвращаем только контакты текущего пользователя
        return Contact.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # При создании контакта автоматически привязываем его к текущему пользователю
        serializer.save(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    """
    API эндпоинт для управления заказами пользователя.
    
    Основные методы:
    - GET: получить список заказов или детали конкретного заказа
    - POST: подтвердить заказ (преобразовать корзину в заказ)
    
    Показывает только подтвержденные заказы (не корзины).
    Требуется аутентификация.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Возвращаем только заказы текущего пользователя, исключая корзины
        return Order.objects.filter(user=self.request.user).exclude(status='new')
    
    def create(self, request):
        """Подтвердить заказ с указанным контактом доставки"""
        # Получаем текущую корзину пользователя
        cart, created = Order.objects.get_or_create(
            user=request.user,
            status='new'
        )
        
        # Получаем ID контакта для доставки
        contact_id = request.data.get('contact_id')
        
        # Проверяем, указан ли контакт
        if not contact_id:
            return Response(
                {'error': 'Contact ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Проверяем, существует ли указанный контакт
        try:
            contact = Contact.objects.get(id=contact_id, user=request.user)
        except Contact.DoesNotExist:
            return Response(
                {'error': 'Contact not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Проверяем, не пуста ли корзина
        if not cart.items.exists():
            return Response(
                {'error': 'Cart is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Меняем статус корзины на "подтвержден"
        cart.status = 'confirmed'
        cart.save()
        
        # Отправляем подтверждение заказа по email пользователю
        subject = 'Order confirmation'
        message = f'Thank you for your order! Your order ID is {cart.id}.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [request.user.email]
        
        try:
            send_mail(subject, message, from_email, recipient_list)
        except Exception as e:
            print(f"Error sending email to user: {e}")
        
        # Отправляем детали заказа администратору
        admin_subject = f'New order #{cart.id}'
        admin_message = f'New order from {request.user.get_full_name() or request.user.username}\n'
        admin_message += f'Contact: {contact.value}\n\n'
        
        for item in cart.items.all():
            admin_message += f'- {item.product.name} from {item.shop.name}: {item.quantity} pcs\n'
        
        admin_email = settings.ADMIN_EMAIL
        
        try:
            send_mail(admin_subject, admin_message, from_email, [admin_email])
        except Exception as e:
            print(f"Error sending email to admin: {e}")
        
        # Возвращаем данные подтвержденного заказа
        return Response(OrderSerializer(cart).data)
