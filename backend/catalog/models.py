from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('sort_order', 'name')
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    image = models.CharField(max_length=255)
    price = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0)
    is_coffee = models.BooleanField(default=False)
    origin = models.CharField(max_length=100, blank=True, null=True)
    roast = models.CharField(max_length=100, blank=True, null=True)
    arabica = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    source = models.URLField(blank=True)
    source_note = models.TextField(blank=True)

    class Meta:
        ordering = ('id',)
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
