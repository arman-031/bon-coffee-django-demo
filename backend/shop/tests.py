from django.contrib.auth import get_user_model
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product
from shop.models import CartItem, Favorite, Order

User = get_user_model()


class ShopApiTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='قهوه', slug='coffee')
        self.product = Product.objects.create(
            id=1,
            name='قهوه تست',
            slug='coffee-test',
            category=self.category,
            image='assets/coffee-1.webp',
            price=100000,
            stock=5,
            is_coffee=True,
            origin='برزیل',
            roast='مدیوم',
            arabica=50,
            description='تست',
            source='https://example.com',
            source_note='نمونه',
        )
        self.user = User.objects.create_user(username='buyer', password='secret1234', email='buyer@example.com')

    def test_registration_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'complexpass123',
            'first_name': 'رضا',
            'last_name': 'احمدی',
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(self.client.get('/api/auth/profile/').status_code, 200)

    def test_csrf_endpoint_sets_cookie_and_authenticated_posts_require_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.get('/api/auth/csrf/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', response.cookies)

        payload = {'product_id': self.product.id}
        blocked = client.post('/api/favorites/', payload, content_type='application/json')
        self.assertEqual(blocked.status_code, 403)

        token = client.cookies['csrftoken'].value
        accepted = client.post(
            '/api/favorites/',
            payload,
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(accepted.status_code, 201)

    def test_login_requires_csrf_and_sets_authenticated_session(self):
        client = Client(enforce_csrf_checks=True)
        payload = {'username': 'buyer', 'password': 'secret1234'}

        blocked = client.post('/api/auth/login/', payload, content_type='application/json')
        self.assertEqual(blocked.status_code, 403)

        client.get('/api/auth/csrf/')
        token = client.cookies['csrftoken'].value
        accepted = client.post(
            '/api/auth/login/',
            payload,
            content_type='application/json',
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(accepted.status_code, 200)
        self.assertIn('sessionid', client.cookies)

    def test_favorites_and_cart_work(self):
        self.client.force_login(self.user)
        fav_response = self.client.post('/api/favorites/', {'product_id': self.product.id}, content_type='application/json')
        self.assertEqual(fav_response.status_code, 201)
        self.assertTrue(Favorite.objects.filter(user=self.user, product=self.product).exists())

        cart_response = self.client.post('/api/cart/', {
            'product_id': self.product.id,
            'quantity': 2,
            'weight': 250,
            'grind': 'اسپرسو',
        }, content_type='application/json')
        self.assertEqual(cart_response.status_code, 201)
        self.assertEqual(CartItem.objects.get(user=self.user, product=self.product).quantity, 2)

    def test_order_creation_and_payment(self):
        self.client.force_login(self.user)
        order_response = self.client.post('/api/orders/create/', {
            'customer_name': 'رضا',
            'phone': '09120000000',
            'address': 'تهران',
            'items': [{'product_id': self.product.id, 'quantity': 2, 'weight': 250, 'grind': 'اسپرسو'}],
        }, content_type='application/json')
        self.assertEqual(order_response.status_code, 201)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total, 2 * self.product.price + 65000)
        self.assertEqual(order.status, Order.STATUS_PENDING)

        payment_response = self.client.post('/api/payments/simulated/', {'order_id': order.id}, content_type='application/json')
        self.assertEqual(payment_response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')

    def test_order_uses_server_pricing_and_selected_coffee_weight(self):
        self.client.force_login(self.user)
        response = self.client.post('/api/orders/create/', {
            'customer_name': 'رضا',
            'phone': '09120000000',
            'address': 'تهران',
            'items': [{'product_id': self.product.id, 'quantity': 1, 'weight': 500, 'grind': 'فرنچ پرس'}],
            'shipping_fee': 0,
            'discount': 999999,
        }, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.subtotal, self.product.price * 2)
        self.assertEqual(order.shipping_fee, 65000)
        self.assertEqual(order.discount, 0)
