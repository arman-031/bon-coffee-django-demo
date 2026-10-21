from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Product.objects.select_related('category')
        category = self.request.query_params.get('category')
        name = self.request.query_params.get('search') or self.request.query_params.get('q')
        arabica = self.request.query_params.get('arabica')

        if category:
            queryset = queryset.filter(category__slug=category)
        if name:
            queryset = queryset.filter(
                Q(name__icontains=name)
                | Q(description__icontains=name)
                | Q(category__name__icontains=name)
            )
        if arabica is not None:
            if arabica == '100':
                queryset = queryset.filter(arabica=100)
            elif arabica == '50':
                queryset = queryset.filter(arabica=50)
            elif arabica == '0':
                queryset = queryset.filter(arabica=0)

        return queryset


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.select_related('category')
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]


class ProductByIdView(generics.RetrieveAPIView):
    queryset = Product.objects.select_related('category')
    serializer_class = ProductSerializer
    lookup_field = 'id'
    permission_classes = [AllowAny]
