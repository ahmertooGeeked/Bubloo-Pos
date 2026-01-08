from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.custom_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # POS
    path('', views.pos_dashboard, name='pos_dashboard'),
    path('place-order/', views.place_order, name='place_order'),

    # Kitchen
    path('kitchen/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('order-status/<int:order_id>/<str:new_status>/', views.update_order_status, name='update_order_status'),

    # Manager / Tables
    path('tables/', views.table_dashboard, name='table_dashboard'),
    path('checkout/<int:table_id>/', views.checkout_table, name='checkout_table'),

    # NEW: Settle Takeaway
    path('settle-order/<int:order_id>/', views.settle_order, name='settle_order'),

    # Reports
    path('report/', views.sales_dashboard, name='sales_dashboard'),

    path('bill/<int:order_id>/', views.generate_bill, name='generate_bill'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('invoice/<int:order_id>/', views.digital_bill, name='digital_bill'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
]
