from django.contrib.auth.models import AbstractUser
from django.db import models

from config import settings


class CustomUser(AbstractUser):
    username = models.CharField(unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, blank=True)

    class Meta:
        db_table = 'custom_user'

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",
        related_query_name="custom_user",
    )


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f'{self.user.username} profile'


class Product(models.Model):
    description = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    quantity = models.IntegerField(max_length=255)
    retail_price = models.DecimalField(max_digits=255)
    wholesale_price = models.DecimalField(max_digits=255, decimal_places=5)


class WatchList(models.Model):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watched_users')
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='watched_products')


class Permission(models.Model):
    value = models.CharField(max_length=255)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='permission_user')


class Order(models.Model):
    data_placed = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=255, blank=True)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='order_user')


class OrderItem(models.Model):
    purchase_price = models.DecimalField(max_digits=255)
    quantity = models.IntegerField(max_length=255)
    wholesale_price = models.DecimalField(max_length=255)
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orderitem_order')
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orderitem_product')