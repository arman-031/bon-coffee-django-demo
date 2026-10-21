from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'sort_order')


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    category_slug = serializers.SerializerMethodField()
    isCoffee = serializers.BooleanField(source='is_coffee', read_only=True)
    sourceNote = serializers.CharField(source='source_note', read_only=True, allow_blank=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'category',
            'category_slug',
            'image',
            'price',
            'stock',
            'isCoffee',
            'origin',
            'roast',
            'arabica',
            'description',
            'source',
            'sourceNote',
        )

    def get_category(self, obj) -> str:
        return obj.category.name

    def get_category_slug(self, obj) -> str:
        return obj.category.slug
