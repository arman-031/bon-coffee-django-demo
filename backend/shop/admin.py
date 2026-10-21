from django.contrib import admin

from .models import CartItem, CustomerProfile, Favorite, Order, OrderItem, PaymentRecord


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'city')
    search_fields = ('user__username', 'phone', 'city')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'weight', 'grind')
    search_fields = ('user__username', 'product__name')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_ref', 'user', 'status', 'total', 'created_at')
    list_filter = ('status',)
    search_fields = ('order_ref', 'user__username', 'customer_name', 'phone')
    inlines = [OrderItemInline]


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('order', 'method', 'amount', 'status', 'is_simulated')
    list_filter = ('is_simulated', 'status')
