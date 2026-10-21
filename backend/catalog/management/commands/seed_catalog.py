import ast
import re
from pathlib import Path

from django.core.management.base import BaseCommand

from catalog.models import Category, Product


class Command(BaseCommand):
    help = 'Seed catalog from the existing frontend product list.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--if-empty',
            action='store_true',
            help='Skip seeding when the database already has products.',
        )

    def handle(self, *args, **options):
        if options['if_empty'] and Product.objects.exists():
            self.stdout.write('Catalog already contains products; seeding skipped.')
            return

        frontend_root = Path(__file__).resolve().parents[4]
        products_file = frontend_root / 'products.js'
        if not products_file.exists():
            self.stderr.write(self.style.ERROR('Missing frontend products.js source; cannot seed catalog.'))
            return

        text = products_file.read_text(encoding='utf-8')
        match = re.search(r'window\.PRODUCTS\s*=\s*(\[[\s\S]*?\])\s*;', text)
        if not match:
            self.stderr.write(self.style.ERROR('Could not find window.PRODUCTS in frontend products.js.'))
            return

        raw = match.group(1)
        raw = re.sub(r'(?<!["\'])\b([A-Za-z_][A-Za-z0-9_]*)\s*:', r'"\1":', raw)
        raw = re.sub(r'\btrue\b', 'True', raw)
        raw = re.sub(r'\bfalse\b', 'False', raw)
        raw = re.sub(r'\bnull\b', 'None', raw)
        raw = re.sub(r'\bundefined\b', 'None', raw)

        try:
            data = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            self.stderr.write(self.style.ERROR('Could not parse frontend products.js into Python objects.'))
            return

        for item in data:
            category, _ = Category.objects.get_or_create(
                name=item['category'],
                defaults={'slug': item['category']},
            )
            Product.objects.update_or_create(
                id=item['id'],
                defaults={
                    'name': item['name'],
                    'slug': str(item['id']),
                    'category': category,
                    'image': item['image'],
                    'price': item['price'],
                    'stock': item['stock'],
                    'is_coffee': item.get('isCoffee', False),
                    'origin': item.get('origin'),
                    'roast': item.get('roast'),
                    'arabica': item.get('arabica', 0),
                    'description': item.get('description', ''),
                    'source': item.get('source', ''),
                    'source_note': item.get('sourceNote', ''),
                },
            )

        self.stdout.write(self.style.SUCCESS('Catalog seeded from frontend data.'))
