from django.urls import path
from . import views

app_name = 'cafe'

urlpatterns = [
    path('', views.cashier_view, name='cashier'),
    path('menu/', views.menu_management_view, name='menu_management'),
    path('statistics/', views.statistics_view, name='statistics'),
    path('orders/', views.orders_view, name='orders'),
    
    # API endpoints
    path('api/menu/', views.api_menu, name='api_menu'),
    path('api/order/create/', views.api_create_order, name='api_create_order'),
    path('api/order/<int:order_id>/print/', views.api_print_receipt, name='api_print_receipt'),
    path('api/orders/', views.api_orders, name='api_orders'),
    path('api/orders/<int:order_id>/', views.api_order_detail, name='api_order_detail'),
    path('api/statistics/', views.api_statistics, name='api_statistics'),
    
    # Category Management API
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/categories/<int:category_id>/', views.api_category_detail, name='api_category_detail'),
    
    # Menu Items Management API
    path('api/items/', views.api_items, name='api_items'),
    path('api/items/<int:item_id>/', views.api_item_detail, name='api_item_detail'),
]
