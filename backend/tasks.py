from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

@shared_task
def send_order_confirmation_email(order_id, user_email, user_name):
    """
    Асинхронная задача для отправки подтверждения заказа по email
    """
    logger.info(f"Sending order confirmation email for order {order_id} to {user_email}")
    
    # Искусственная задержка для демонстрации асинхронной обработки
    time.sleep(2)
    
    try:
        subject = f'Заказ №{order_id} подтвержден'
        message = f'Здравствуйте, {user_name}!\n\nВаш заказ №{order_id} успешно подтвержден и передан в обработку.\n\nС уважением,\nКоманда нашего магазина.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user_email]
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        logger.info(f"Order confirmation email sent successfully for order {order_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send order confirmation email for order {order_id}: {e}")
        return False

@shared_task
def update_product_availability(shop_id):
    """
    Асинхронная задача для обновления доступности товаров в магазине
    """
    from backend.models import Shop, ProductInfo
    
    logger.info(f"Updating product availability for shop {shop_id}")
    
    # Искусственная задержка для демонстрации асинхронной обработки
    time.sleep(5)
    
    try:
        # Получаем все продукты магазина
        products = ProductInfo.objects.filter(shop_id=shop_id)
        
        # Обновляем количество товаров (демонстрационная логика)
        for product in products:
            # Здесь в реальном приложении может быть сложная логика обновления
            # с проверкой внешних API или другими вычислениями
            logger.info(f"Processing product {product.id} - {product.name}")
        
        logger.info(f"Successfully updated availability for {products.count()} products in shop {shop_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update product availability for shop {shop_id}: {e}")
        return False

@shared_task
def update_all_shops_availability():
    """
    Периодическая задача для обновления доступности товаров во всех магазинах
    """
    from backend.models import Shop
    
    logger.info("Starting update of product availability for all shops")
    
    try:
        # Получаем все магазины из базы данных
        shops = Shop.objects.all()
        
        if not shops.exists():
            logger.warning("No shops found in the database")
            return "No shops found to update"
        
        # Для каждого магазина создаем отдельную асинхронную задачу
        for shop in shops:
            logger.info(f"Scheduling update for shop {shop.id} - {shop.name}")
            # Запускаем задачу update_product_availability для каждого магазина
            update_product_availability.delay(shop.id)
        
        return f"Scheduled updates for {shops.count()} shops"
    except Exception as e:
        logger.error(f"Error scheduling shop updates: {e}")
        return False

@shared_task
def process_new_orders():
    """
    Периодическая задача для обработки новых заказов
    """
    from backend.models import Order
    
    logger.info("Processing new orders")
    
    try:
        # Получаем все новые заказы
        new_orders = Order.objects.filter(status='new')
        
        # Обрабатываем каждый заказ
        for order in new_orders:
            logger.info(f"Processing order {order.id}")
            # Здесь может быть логика обработки заказа
            
            # Пример: автоматическое подтверждение заказа
            order.status = 'confirmed'
            order.save()
            
            # Отправляем уведомление по email асинхронно
            send_order_confirmation_email.delay(
                order.id, 
                order.user.email, 
                f"{order.user.first_name} {order.user.last_name}"
            )
        
        return f"Processed {new_orders.count()} new orders"
    except Exception as e:
        logger.error(f"Error processing new orders: {e}")
        return False

@shared_task
def create_image_thumbnails(model, instance_id, field_name):
    """
    Асинхронно создает все миниатюры для изображения после его загрузки
    
    Args:
        model (str): Строковое имя модели ('UserProfile' или 'Product')
        instance_id (int): ID экземпляра модели
        field_name (str): Имя поля с изображением ('avatar' или 'image')
    """
    logger.info(f"Creating thumbnails for {model} with id {instance_id}, field {field_name}")
    
    try:
        from django.apps import apps
        from django.conf import settings
        from versatileimagefield.image_warmer import VersatileImageFieldWarmer
        
        # Получаем класс модели
        Model = apps.get_model('backend', model)
        instance = Model.objects.get(id=instance_id)
        
        # Получаем ссылку на поле с изображением
        image_field = getattr(instance, field_name)
        
        # Пропускаем, если изображения нет
        if not image_field:
            logger.info(f"No image found for {model} with id {instance_id}")
            return False
        
        # Получаем набор размеров для создания
        if model == 'UserProfile':
            rendition_key_set = 'user_avatar'
        elif model == 'Product':
            rendition_key_set = 'product_image'
        else:
            logger.error(f"Unknown model {model}")
            return False
        
        rendition_keys = settings.VERSATILEIMAGEFIELD_RENDITION_KEY_SETS.get(rendition_key_set, [])
        
        # Создаем все миниатюры
        warmer = VersatileImageFieldWarmer(
            instance_or_queryset=instance,
            rendition_key_set=rendition_keys,
            image_attr=field_name,
            verbose=True
        )
        
        num_created, failed_to_create = warmer.warm()
        
        logger.info(
            f"Created {num_created} thumbnails for {model} with id {instance_id}, "
            f"failed to create {failed_to_create or 0}"
        )
        
        return {
            'success': True,
            'created': num_created,
            'failed': failed_to_create or 0
        }
        
    except Exception as e:
        logger.error(f"Error creating thumbnails for {model} with id {instance_id}: {e}")
        return {
            'success': False,
            'error': str(e)
        } 