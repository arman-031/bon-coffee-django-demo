from django.urls import path

from .views import CategoryListView, ProductByIdView, ProductDetailView, ProductListView

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='categories'),
    path('products/', ProductListView.as_view(), name='products'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/id/<int:id>/', ProductByIdView.as_view(), name='product-id'),
]
