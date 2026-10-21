from django.urls import path

from .views import (
    CartSummaryView,
    CartView,
    CsrfTokenView,
    FavoriteDeleteView,
    FavoriteListView,
    LoginView,
    LogoutView,
    OrderCreateView,
    OrderDetailView,
    OrderListView,
    ProfileView,
    RegisterView,
    SimulatedPaymentView,
)

urlpatterns = [
    path('auth/csrf/', CsrfTokenView.as_view(), name='csrf-token'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('favorites/', FavoriteListView.as_view(), name='favorites'),
    path('favorites/<int:product_id>/', FavoriteDeleteView.as_view(), name='favorite-delete'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/summary/', CartSummaryView.as_view(), name='cart-summary'),
    path('orders/', OrderListView.as_view(), name='orders'),
    path('orders/create/', OrderCreateView.as_view(), name='order-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('payments/simulated/', SimulatedPaymentView.as_view(), name='simulated-payment'),
]
