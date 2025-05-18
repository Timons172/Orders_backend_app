from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegisterView, UserLoginView, ProductViewSet, ProductInfoViewSet,
    CartView, ContactViewSet, OrderViewSet, UserAvatarView, ProductImageView
)

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'product-info', ProductInfoViewSet)
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('user/register/', UserRegisterView.as_view(), name='user-register'),
    path('user/login/', UserLoginView.as_view(), name='user-login'),
    path('user/avatar/', UserAvatarView.as_view(), name='user-avatar'),
    path('cart/', CartView.as_view(), name='cart'),
    path('products/<int:product_id>/image/', ProductImageView.as_view(), name='product-image'),
] 