from django.urls import path
from . import views

# Main URL routing configurations for the public storefront views.
urlpatterns = [

    # HOME
    path('', views.index, name='index'),

    # AUTH
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register, name='register'),

    # CATEGORY
    path('categories/<int:id>/', views.category_view, name='category_view'),
    path('subcategory/<int:id>/', views.subcategory_view, name='subcategory_view'),

    # PRODUCT
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('shop/', views.shop, name='shop'),
    path('search/', views.search, name='search'),

    # CART
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/increase/<int:product_id>/', views.cart_increase_quantity, name='cart_increase_quantity'),
    path('cart/decrease/<int:product_id>/', views.cart_decrease_quantity, name='cart_decrease_quantity'),

    # CHECKOUT
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/increase/<int:product_id>/', views.checkout_increase, name='checkout_increase'),
    path('checkout/decrease/<int:product_id>/', views.checkout_decrease, name='checkout_decrease'),

    # PAYMENT
    path('payment-success/', views.payment_success, name='payment_success'),

    # ORDER
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('orders/', views.order_history, name='order_history'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('order-tracking/<int:id>/', views.order_tracking, name='order_tracking'),

    # BUY NOW
    path('buy-now/<int:product_id>/', views.buy_now, name='buy_now'),

    # WISHLIST
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_wishlist, name='remove_wishlist'),

    # CONTACT
    path('contact/', views.contact, name='contact'),
]