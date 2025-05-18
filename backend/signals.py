from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile, Product
from .tasks import create_image_thumbnails


@receiver(post_save, sender=UserProfile)
def process_user_avatar(sender, instance, created, **kwargs):
    """
    Сигнал для асинхронного создания миниатюр аватара пользователя после сохранения профиля.
    """
    # Проверяем, что профиль уже создан (не новый) и имеет аватар
    if not created and instance.avatar:
        # Запускаем асинхронную задачу по созданию миниатюр
        create_image_thumbnails.delay(
            model='UserProfile',
            instance_id=instance.id,
            field_name='avatar'
        )


@receiver(post_save, sender=Product)
def process_product_image(sender, instance, created, **kwargs):
    """
    Сигнал для асинхронного создания миниатюр изображения товара после сохранения товара.
    """
    # Проверяем, что у товара есть изображение
    if instance.image:
        # Запускаем асинхронную задачу по созданию миниатюр
        create_image_thumbnails.delay(
            model='Product',
            instance_id=instance.id,
            field_name='image'
        ) 