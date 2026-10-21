from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'stock', 'is_coffee')
    list_filter = ('category', 'is_coffee')
    search_fields = ('name', 'description', 'source_note')
    list_editable = ('price', 'stock')
