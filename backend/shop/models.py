import uuid

from django.conf import settings
from django.db import models

from catalog.models import Product


def generate_order_ref():
    return uuid.uuid4().hex[:12].upper()


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=80, blank=True)
    address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f'{self.user} -> {self.product}'


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    weight = models.PositiveIntegerField(default=250)
    grind = models.CharField(max_length=80, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product', 'weight', 'grind')

    def __str__(self):
        return f'{self.user} / {self.product} / {self.quantity}'

    @property
    def unit_price(self) -> int:
        if self.product.is_coffee and self.weight:
            return self.product.price * self.weight // 250
        return self.product.price

    @property
    def line_total(self) -> int:
        return self.quantity * self.unit_price


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_PREPARING = 'preparing'
    STATUS_SHIPPED = 'shipped'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'در انتظار'),
        (STATUS_PAID, 'پرداخت شده'),
        (STATUS_PREPARING, 'در حال آماده‌سازی'),
        (STATUS_SHIPPED, 'ارسال شده'),
        (STATUS_COMPLETED, 'تکمیل شده'),
        (STATUS_CANCELLED, 'لغو شده'),
    ]

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    order_ref = models.CharField(max_length=32, unique=True, default=generate_order_ref)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    customer_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    address = models.TextField()
    postal_code = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    subtotal = models.PositiveIntegerField(default=0)
    shipping_fee = models.PositiveIntegerField(default=0)
    discount = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Order {self.order_ref}'

    def finalize_amounts(self):
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.total = self.subtotal + self.shipping_fee - self.discount
        self.total = max(self.total, 0)
        return self.total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    product_name = models.CharField(max_length=255)
    unit_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)
    weight = models.PositiveIntegerField(default=250)
    grind = models.CharField(max_length=80, blank=True, default='')
    line_total = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.line_total = self.unit_price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'


class PaymentRecord(models.Model):
    METHOD_SIMULATED = 'simulated'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=30, default=METHOD_SIMULATED)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default='paid')
    provider = models.CharField(max_length=80, default='demo-gateway')
    created_at = models.DateTimeField(auto_now_add=True)
    is_simulated = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.order.order_ref} - {self.status}'
