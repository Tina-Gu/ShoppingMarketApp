"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.web.views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', UserRegistrationCreateAPIView.as_view(), name='register'),
    path('login/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', UserRegistrationCreateAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetail.as_view(), name='product_detail'), #
    path('orders/<int:pk>/', OrderDetail.as_view(), name='order_detail'),
    path('orders/', UserOrdersList.as_view(), name='user_orders'),
    path('orders/top-frequently-purchased/', TopFrequentlyPurchasedItemsList.as_view(), name='top_frequently_purchased'),
    path('watchlist/add/', AddToWatchListView.as_view(), name='add_watchlist'),
    path('watchlist/remove/<int:product_id>/', RemoveFromWatchListView.as_view(), name='remove_watchlist'),
    path('watchlist/', WatchListView.as_view(), name='watchlist'),
    # admin
    path('dashboard/orders/', OrderListView.as_view(), name='dashboard_orders'),
    path('products/add/', ProductCreateAPIView.as_view(), name='add_product'),
    path('orders/update/<int:pk>/', UpdateOrderStatusView.as_view(), name='update_order_status'),
    path('products/most-profitable/', MostProfitableProductView.as_view(), name='most_profitable_product'),
    path('products/top-sold/', TopSoldProductsView.as_view(), name='top-sold-products'),
    path('sales/total-items-sold/', TotalItemsSoldView.as_view(), name='total-items-sold'),


]
