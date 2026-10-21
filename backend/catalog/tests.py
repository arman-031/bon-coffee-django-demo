from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product


class CatalogApiTests(TestCase):
    def setUp(self):
        self.category_1 = Category.objects.create(name='قهوه', slug='coffee')
        self.category_2 = Category.objects.create(name='قهوه‌سازها', slug='coffee-makers')
        self.product_1 = Product.objects.create(
            id=1,
            name='قهوه باریستا ۵۰٪ عربیکا و ۵۰٪ روبوستا',
            slug='1',
            category=self.category_1,
            image='assets/coffee-1.webp',
            price=1375000,
            stock=12,
            is_coffee=True,
            origin='ترکیبی',
            roast='مدیوم',
            arabica=50,
            description='ترکیب برابر عربیکا و روبوستا؛ انتخاب نوع آسیاب را متناسب با ابزار دم‌آوری انجام بده.',
            source='https://www.melocoffee.com/',
            source_note='قیمت بازیابی شده.',
        )
        self.product_2 = Product.objects.create(
            id=2,
            name='فرنچ‌پرس شیشه‌ای ۳۵۰ میلی‌لیتر',
            slug='2',
            category=self.category_2,
            image='assets/tool-1.webp',
            price=680000,
            stock=6,
            is_coffee=False,
            description='قهوه‌ساز دستی با بدنه شیشه‌ای.',
            source='https://www.melocoffee.com/',
            source_note='نمونه.',
        )

    def test_categories_endpoint(self):
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_products_list_endpoint(self):
        response = self.client.get(reverse('products'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_product_detail_endpoint(self):
        response = self.client.get(reverse('product-detail', args=[self.product_1.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.product_1.id)

    def test_product_filter_and_search(self):
        response = self.client.get('/api/products/?category=coffee')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        search_response = self.client.get('/api/products/?search=قهوه')
        self.assertEqual(search_response.status_code, 200)
        self.assertGreaterEqual(len(search_response.json()), 1)

    def test_schema_and_swagger_endpoints(self):
        schema_response = self.client.get('/api/schema/')
        self.assertEqual(schema_response.status_code, 200)
        self.assertIn(b'openapi:', schema_response.content)
        self.assertIn(b'/api/auth/login/', schema_response.content)
        self.assertIn(b'/api/orders/create/', schema_response.content)

        docs_response = self.client.get('/api/docs/')
        self.assertEqual(docs_response.status_code, 200)
