from django.contrib.auth import get_user_model
from rest_framework import serializers

from catalog.models import Product
from catalog.serializers import ProductSerializer
from .models import CartItem, CustomerProfile, Favorite, Order, OrderItem, PaymentRecord

User = get_user_model()


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ('phone', 'city', 'address', 'postal_code')


class UserProfileSerializer(serializers.ModelSerializer):
    profile = CustomerProfileSerializer(source='customer_profile', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'profile')


class AuthResponseSerializer(serializers.Serializer):
    user = UserProfileSerializer()
    message = serializers.CharField()


class LoginPayloadSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class ProfileUpdateSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    city = serializers.CharField(max_length=80, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)


class CsrfTokenSerializer(serializers.Serializer):
    csrfToken = serializers.CharField()


class ApiMessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class FavoriteCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)


class FavoriteResultSerializer(serializers.Serializer):
    created = serializers.BooleanField()
    favorite_id = serializers.IntegerField()


class DeleteResultSerializer(serializers.Serializer):
    deleted = serializers.BooleanField()


class CartUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)


class CartDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField(min_value=1)


class CartSummarySerializer(serializers.Serializer):
    items_count = serializers.IntegerField()
    subtotal = serializers.IntegerField()


class PaymentRequestSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(min_value=1)


class PaymentResultSerializer(serializers.Serializer):
    message = serializers.CharField(required=False)
    detail = serializers.CharField(required=False)
    order_ref = serializers.CharField()
    is_simulated = serializers.BooleanField(required=False)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        CustomerProfile.objects.get_or_create(user=user)
        return user


class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'product', 'created_at')


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity', 'weight', 'grind', 'line_total', 'updated_at')


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'unit_price', 'quantity', 'weight', 'grind', 'line_total')


class PaymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRecord
        fields = ('method', 'amount', 'status', 'provider', 'is_simulated', 'created_at')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentRecordSerializer(read_only=True)

    class Meta:
        model = Order
        fields = (
            'id', 'order_ref', 'status', 'customer_name', 'phone', 'email', 'city', 'address', 'postal_code',
            'notes', 'subtotal', 'shipping_fee', 'discount', 'total', 'created_at', 'updated_at', 'paid_at',
            'items', 'payment'
        )


class CartPayloadSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, required=False, default=1)
    weight = serializers.ChoiceField(choices=(0, 250, 500, 1000), required=False, default=250)
    grind = serializers.CharField(required=False, allow_blank=True, default='')


class OrderLineSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)
    weight = serializers.IntegerField(required=False, default=0, min_value=0)
    grind = serializers.CharField(required=False, allow_blank=True, default='')


class OrderCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    city = serializers.CharField(max_length=80, required=False, allow_blank=True)
    address = serializers.CharField()
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(child=OrderLineSerializer(), allow_empty=False)
    coupon_code = serializers.CharField(required=False, allow_blank=True, default='')
