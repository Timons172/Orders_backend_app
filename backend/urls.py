from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserRegisterView, UserLoginView, ProductViewSet, ProductInfoViewSet,
    CartView, ContactViewSet, OrderViewSet
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
    path('cart/', CartView.as_view(), name='cart'),
] 