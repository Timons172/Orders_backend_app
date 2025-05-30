from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem, Contact, UserProfile
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from versatileimagefield.serializers import VersatileImageFieldSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели профиля пользователя.
    Включает поддержку аватара с различными размерами миниатюр.
    """
    avatar = VersatileImageFieldSerializer(
        sizes='user_avatar',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = UserProfile
        fields = ('avatar', 'avatar_ppoi')


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя.
    Используется для отображения данных пользователя в API.
    Включает вложенные данные профиля с аватаром.
    """
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')
        read_only_fields = ('id',)


class ContactSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели контактов пользователя.
    Используется для создания и получения информации об адресах и телефонах.
    """
    class Meta:
        model = Contact
        fields = ('id', 'type', 'value')
        read_only_fields = ('id',)


class ShopSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели магазина/поставщика.
    """
    class Meta:
        model = Shop
        fields = ('id', 'name', 'url')
        read_only_fields = ('id',)


class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели категории товаров.
    Включает вложенные данные о магазинах, в которых доступна категория.
    """
    shops = ShopSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'shops')
        read_only_fields = ('id',)


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели товара.
    Включает вложенные данные о категории товара и изображении с различными миниатюрами.
    """
    category = CategorySerializer(read_only=True)
    image = VersatileImageFieldSerializer(
        sizes='product_image',
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'category', 'image', 'image_ppoi')
        read_only_fields = ('id',)


class ParameterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели параметров товара.
    """
    class Meta:
        model = Parameter
        fields = ('id', 'name')
        read_only_fields = ('id',)


class ProductParameterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели значений параметров товара.
    Включает вложенные данные о самом параметре.
    """
    parameter = ParameterSerializer(read_only=True)

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


class ProductInfoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели информации о товаре.
    Включает вложенные данные о товаре, магазине и параметрах.
    Используется для детального отображения товара с ценами и характеристиками.
    """
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    parameters = ProductParameterSerializer(many=True, read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'product', 'shop', 'name', 'quantity', 'price', 'price_rrc', 'parameters')
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели элемента заказа.
    Используется для получения данных о товарах в заказе.
    Включает вложенные данные о товаре и магазине.
    """
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'shop', 'quantity')
        read_only_fields = ('id',)


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания элемента заказа (добавления товара в корзину).
    Принимает только идентификаторы товара, магазина и количество.
    """
    class Meta:
        model = OrderItem
        fields = ('product', 'shop', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели заказа.
    Включает вложенные данные о товарах в заказе и вычисляет общую сумму заказа.
    """
    items = OrderItemSerializer(many=True, read_only=True)
    total_sum = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ('id', 'dt', 'status', 'items', 'total_sum')
        read_only_fields = ('id',)
    
    def get_total_sum(self, obj):
        """
        Метод для вычисления общей суммы заказа.
        Суммирует стоимость всех товаров в заказе с учетом их количества.
        """
        return sum(item.product.product_infos.get(shop=item.shop).price * item.quantity for item in obj.items.all())


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Пример регистрации',
            value={
                "username": "user123",
                "email": "user@example.com",
                "first_name": "Иван",
                "last_name": "Иванов",
                "password": "password123",
                "password_repeat": "password123"
            }
        )
    ]
)
class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации новых пользователей.
    Проверяет, что введенные пароли совпадают, и создает нового пользователя.
    """
    password = serializers.CharField(write_only=True)
    password_repeat = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password_repeat')
    
    def validate(self, data):
        """
        Валидация данных: проверяет, что пароли совпадают.
        """
        if data['password'] != data['password_repeat']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        """
        Создает нового пользователя с хешированным паролем.
        """
        validated_data.pop('password_repeat')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Пример логина',
            value={
                "username": "user123",
                "password": "password123"
            }
        )
    ]
)
class UserLoginSerializer(serializers.Serializer):
    """
    Сериализатор для логина пользователя (только username и password).
    """
    username = serializers.CharField()
    password = serializers.CharField() 