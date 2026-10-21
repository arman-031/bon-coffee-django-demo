from decimal import Decimal
from decimal import ROUND_HALF_UP

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import transaction
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from catalog.models import Product
from .models import CartItem, CustomerProfile, Favorite, Order, OrderItem, PaymentRecord
from .serializers import (
    ApiMessageSerializer,
    AuthResponseSerializer,
    CartItemSerializer,
    CartDeleteSerializer,
    CartPayloadSerializer,
    CartSummarySerializer,
    CartUpdateSerializer,
    CsrfTokenSerializer,
    DeleteResultSerializer,
    FavoriteCreateSerializer,
    FavoriteSerializer,
    FavoriteResultSerializer,
    LoginPayloadSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    PaymentRequestSerializer,
    PaymentResultSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)

User = get_user_model()
SHIPPING_FEE = 65_000
FREE_SHIPPING_THRESHOLD = 3_000_000
COUPON_CODE = 'BON10'
COUPON_RATE = Decimal('0.10')


class CsrfTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    @extend_schema(responses=CsrfTokenSerializer)
    def get(self, request):
        return Response({'csrfToken': get_token(request)})


class RegisterView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(request=RegisterSerializer, responses=AuthResponseSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        login(request, user)
        profile = UserProfileSerializer(user)
        return Response({'user': profile.data, 'message': 'ثبت‌نام انجام شد.'}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    @method_decorator(csrf_protect)
    @extend_schema(request=LoginPayloadSerializer, responses=AuthResponseSerializer)
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'detail': 'نام کاربری و رمز عبور لازم است.'}, status=400)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detail': 'نام کاربری یا رمز عبور نامعتبر است.'}, status=401)
        login(request, user)
        return Response({'user': UserProfileSerializer(user).data, 'message': 'ورود موفق بود.'}, status=200)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses=ApiMessageSerializer)
    def post(self, request):
        logout(request)
        return Response({'message': 'خروج با موفقیت انجام شد.'}, status=200)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserProfileSerializer)
    def get(self, request):
        return Response(UserProfileSerializer(request.user).data)

    @extend_schema(request=ProfileUpdateSerializer, responses=UserProfileSerializer)
    def patch(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        profile.phone = request.data.get('phone', profile.phone)
        profile.city = request.data.get('city', profile.city)
        profile.address = request.data.get('address', profile.address)
        profile.postal_code = request.data.get('postal_code', profile.postal_code)
        profile.save()

        user = request.user
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        user.email = request.data.get('email', user.email)
        user.save(update_fields=['first_name', 'last_name', 'email'])

        return Response(UserProfileSerializer(user).data)


class FavoriteListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=FavoriteSerializer(many=True))
    def get(self, request):
        favorites = Favorite.objects.filter(user=request.user).select_related('product').order_by('-created_at')
        return Response(FavoriteSerializer(favorites, many=True).data)

    @extend_schema(request=FavoriteCreateSerializer, responses=FavoriteResultSerializer)
    def post(self, request):
        product_id = request.data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        fav, created = Favorite.objects.get_or_create(user=request.user, product=product)
        return Response({'created': created, 'favorite_id': fav.id}, status=201 if created else 200)


class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=DeleteResultSerializer)
    def delete(self, request, product_id):
        deleted, _ = Favorite.objects.filter(user=request.user, product_id=product_id).delete()
        return Response({'deleted': deleted > 0}, status=200)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CartItemSerializer(many=True))
    def get(self, request):
        items = CartItem.objects.filter(user=request.user).select_related('product')
        return Response(CartItemSerializer(items, many=True).data)

    @extend_schema(request=CartPayloadSerializer, responses=CartItemSerializer)
    def post(self, request):
        serializer = CartPayloadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        payload = serializer.validated_data
        product = get_object_or_404(Product, id=payload['product_id'])
        if product.stock <= 0:
            return Response({'detail': 'محصول ناموجود است.'}, status=400)

        item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            weight=payload.get('weight', 250),
            grind=payload.get('grind', ''),
            defaults={'quantity': payload.get('quantity', 1)},
        )
        if not created:
            item.quantity = min(item.quantity + payload.get('quantity', 1), product.stock)
            item.save(update_fields=['quantity', 'updated_at'])
        return Response(CartItemSerializer(item).data, status=201 if created else 200)

    @extend_schema(request=CartUpdateSerializer, responses=CartItemSerializer)
    def patch(self, request):
        item_id = request.data.get('id')
        quantity = int(request.data.get('quantity', 0))
        if not item_id or quantity < 1:
            return Response({'detail': 'تعداد نامعتبر است.'}, status=400)
        item = get_object_or_404(CartItem, id=item_id, user=request.user)
        item.quantity = min(quantity, item.product.stock)
        item.save(update_fields=['quantity', 'updated_at'])
        return Response(CartItemSerializer(item).data)

    @extend_schema(request=CartDeleteSerializer, responses=DeleteResultSerializer)
    def delete(self, request):
        item_id = request.data.get('id')
        if not item_id:
            return Response({'detail': 'آیتم نامعتبر است.'}, status=400)
        deleted, _ = CartItem.objects.filter(id=item_id, user=request.user).delete()
        return Response({'deleted': deleted > 0}, status=200)


class CartSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CartSummarySerializer)
    def get(self, request):
        items = CartItem.objects.filter(user=request.user).select_related('product')
        subtotal = sum(item.line_total for item in items)
        return Response({'items_count': sum(item.quantity for item in items), 'subtotal': subtotal})


class OrderCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=OrderCreateSerializer, responses=OrderSerializer)
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        payload = serializer.validated_data
        items = payload['items']
        if not items:
            return Response({'detail': 'سبد خرید خالی است.'}, status=400)
        coupon_code = payload['coupon_code'].strip().upper()
        if coupon_code and coupon_code != COUPON_CODE:
            return Response({'detail': 'کد تخفیف معتبر نیست.'}, status=400)

        try:
            with transaction.atomic():
                product_ids = {item['product_id'] for item in items}
                locked_products = Product.objects.select_for_update().filter(
                    id__in=product_ids,
                ).in_bulk()
                quantities = {}
                products = []
                for raw in items:
                    product = locked_products.get(raw['product_id'])
                    if product is None:
                        raise ValueError('یکی از محصولات سفارش پیدا نشد.')
                    quantity = raw['quantity']
                    weight = raw['weight']
                    grind = raw['grind']
                    if product.is_coffee:
                        if weight not in (250, 500, 1000) or not grind:
                            raise ValueError('وزن و آسیاب قهوه را بررسی کنید.')
                        unit_price = product.price * weight // 250
                    else:
                        if weight:
                            raise ValueError('وزن برای این محصول معتبر نیست.')
                        unit_price = product.price
                    quantities[product.id] = quantities.get(product.id, 0) + quantity
                    products.append({
                        'product': product,
                        'qty': quantity,
                        'weight': weight,
                        'grind': grind,
                        'unit_price': unit_price,
                    })

                for product_id, quantity in quantities.items():
                    product = locked_products[product_id]
                    if quantity > product.stock:
                        raise ValueError(f'موجودی {product.name} کافی نیست.')

                subtotal = sum(item['unit_price'] * item['qty'] for item in products)
                shipping_fee = (
                    0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE
                )
                discount = (
                    int((Decimal(subtotal) * COUPON_RATE).quantize(
                        Decimal('1'),
                        rounding=ROUND_HALF_UP,
                    ))
                    if coupon_code
                    else 0
                )
                total = subtotal + shipping_fee - discount
                order = Order.objects.create(
                    user=request.user,
                    customer_name=payload['customer_name'],
                    phone=payload['phone'],
                    email=payload.get('email', ''),
                    city=payload.get('city', ''),
                    address=payload['address'],
                    postal_code=payload.get('postal_code', ''),
                    notes=payload.get('notes', ''),
                    subtotal=subtotal,
                    shipping_fee=shipping_fee,
                    discount=discount,
                    total=max(total, 0),
                )

                for item in products:
                    product = item['product']
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        product_name=product.name,
                        unit_price=item['unit_price'],
                        quantity=item['qty'],
                        weight=int(item['weight']),
                        grind=item['grind'],
                    )

                for product_id, quantity in quantities.items():
                    product = locked_products[product_id]
                    product.stock -= quantity
                    product.save(update_fields=['stock'])

            return Response(OrderSerializer(order).data, status=201)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id='order_list', responses=OrderSerializer(many=True))
    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
        return Response(OrderSerializer(orders, many=True).data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id='order_detail', responses=OrderSerializer)
    def get(self, request, pk):
        order = get_object_or_404(Order, id=pk, user=request.user)
        return Response(OrderSerializer(order).data)


class SimulatedPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=PaymentRequestSerializer, responses=PaymentResultSerializer)
    def post(self, request):
        order_id = request.data.get('order_id')
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.status == Order.STATUS_PAID:
            return Response({'detail': 'این سفارش قبلاً پرداخت شده است.', 'order_ref': order.order_ref}, status=200)
        if order.status != Order.STATUS_PENDING:
            return Response({'detail': 'این سفارش قابل پرداخت نیست.'}, status=400)
        with transaction.atomic():
            order.status = Order.STATUS_PAID
            order.paid_at = timezone.now()
            order.save(update_fields=['status', 'paid_at'])
            PaymentRecord.objects.update_or_create(
                order=order,
                defaults={
                    'amount': order.total,
                    'status': 'paid',
                    'provider': 'demo-gateway',
                    'is_simulated': True,
                },
            )
            for item in order.items.all():
                CartItem.objects.filter(
                    user=request.user,
                    product=item.product,
                    weight=item.weight,
                    grind=item.grind,
                ).delete()
        return Response({'message': 'پرداخت شبیه‌سازی‌شده با موفقیت انجام شد.', 'order_ref': order.order_ref, 'is_simulated': True}, status=200)
