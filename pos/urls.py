from django.urls import path
from . import views

urlpatterns = [
    # Cashier / POS
    path('', views.pos_dashboard, name='pos_dashboard'),
    path('place-order/', views.place_order, name='place_order'),

    # Kitchen / Chef
    path('kitchen/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('order-status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),
    path('tables/', views.table_dashboard, name='table_dashboard'),
    path('checkout/<int:table_id>/', views.checkout_table, name='checkout_table'),

    path('login/', views.custom_login, name='login'),
        path('logout/', views.user_logout, name='logout'),
        path('report/', views.sales_dashboard, name='sales_dashboard'),
]
