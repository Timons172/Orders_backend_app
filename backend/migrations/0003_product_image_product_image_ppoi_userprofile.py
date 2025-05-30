# Generated by Django 5.2.1 on 2025-05-18 19:30

import django.db.models.deletion
import versatileimagefield.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_order_contact'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to='product_images/', verbose_name='Изображение товара'),
        ),
        migrations.AddField(
            model_name='product',
            name='image_ppoi',
            field=versatileimagefield.fields.PPOIField(default='0.5x0.5', editable=False, max_length=20, verbose_name='Точка интереса изображения товара'),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to='user_avatars/', verbose_name='Аватар')),
                ('avatar_ppoi', versatileimagefield.fields.PPOIField(default='0.5x0.5', editable=False, max_length=20, verbose_name='Точка интереса аватара')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User profile',
                'verbose_name_plural': 'User profiles',
            },
        ),
    ]
