import json
import logging
from decimal import Decimal

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone as dj_timezone
from django.views.decorators.csrf import csrf_exempt

from .forms import RegisterForm, ReviewForm
from .models import *

logger = logging.getLogger(__name__)



def home(request):
    """
    View to redirect administrative accounts to admin panel,
    or render index.html for general storefront users.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('/admin/')

    return render(request, 'index.html')

def register(request):
    """
    View to register a new customer account using RegisterForm.
    """

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('login')

    else:
        form = RegisterForm()

    return render(request,'register.html',{'form':form})

def user_login(request):
    """
    View to log in users while preventing admin users from logging in via storefront.
    """
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            # 🔥 BLOCK ADMIN HERE
            if user.is_staff:
                return render(request, 'login.html', {
                    'form': form,
                    'error': 'Admin should login from admin panel'
                })

            login(request, user)
            return redirect('index')

    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def user_logout(request):
    is_admin = request.user.is_staff
    logout(request)

    if is_admin:
        return redirect('/admin/')
    return redirect('index')

def index(request):
    """
    View to display categories and a subset of featured products on the homepage.
    """
    categories = Cateogry.objects.all() 
    products = Products.objects.all()[:12]
    cart_count = 0
    if request.user.is_authenticated:
        cart_count=Cart.objects.filter(user=request.user).count()
    return render(request, 'index.html', {'categories': categories,'cart_count':cart_count,'products':products})


def category_view(request, id):
    """
    View to render all subcategories under a specific parent category ID.
    """

    category = get_object_or_404(Cateogry, id=id)

    subcategories = Subcategory.objects.filter(category=category)

    categories = Cateogry.objects.all()

    return render(request, 'category.html', {
        'category': category,
        'subcategories': subcategories,
        'categories': categories
    })

def subcategory_view(request, id):

    subcategory = get_object_or_404(Subcategory, id=id)

    products = Products.objects.filter(
        category=subcategory.category,
        subcategory=subcategory
    )

    categories = Cateogry.objects.all()

    return render(request, 'subcategory.html', {
        'products': products,
        'subcategory': subcategory,
        'categories': categories
    })

@login_required
def add_to_cart(request, product_id):

    if request.method == "POST":
        product = get_object_or_404(Products, id=product_id)

        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "error"})


@login_required
def cart_detail(request):
    """
    Renders the cart details page showing items, quantities, and subtotal.
    """
    cart_items = Cart.objects.filter(user=request.user)

    total = sum(item.total_price() for item in cart_items)

    categories = Cateogry.objects.all()

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'categories': categories
    })


@login_required
def remove_from_cart(request, product_id):

    cart_item = Cart.objects.filter(
        user=request.user,
        product_id=product_id
    ).first()

    if cart_item:
        cart_item.delete()

    return redirect('cart_detail')


@login_required
def cart_increase_quantity(request, product_id):

    cart_item = Cart.objects.filter(
        user=request.user,
        product_id=product_id
    ).first()

    if cart_item:
        # ✅ prevent exceeding stock
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.error(request, "Stock limit reached!")

    return redirect('cart_detail')

@login_required
def cart_decrease_quantity(request, product_id):

    cart_item = Cart.objects.filter(
        user=request.user,
        product_id=product_id
    ).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('cart_detail')



@login_required
def checkout(request):
    """
    Handles checkout logic including address selection, coupon code application,
    order placement, and payment integration (COD or Razorpay).
    """
    cart_items = Cart.objects.filter(user=request.user)
    addresses = Address.objects.filter(user=request.user)

    subtotal = sum(item.total_price() for item in cart_items)

    discount = Decimal("0")
    coupon_code = None
    error = None

    if request.method == "POST":

        # =========================
        # APPLY COUPON
        # =========================
        if 'apply_coupon' in request.POST:
            code = request.POST.get('coupon_code') or request.POST.get('apply_coupon')

            try:
                coupon = Coupon.objects.get(code=code, active=True)

                if coupon.valid_from <= dj_timezone.now() <= coupon.valid_to:
                    discount = (Decimal(coupon.discount) / Decimal("100")) * subtotal

                    request.session['coupon'] = coupon.code
                    request.session['discount'] = str(discount)

                    return redirect('checkout')
                else:
                    error = "Coupon expired"

            except Coupon.DoesNotExist:
                error = "Invalid coupon"

        # =========================
        # SAVE ADDRESS
        # =========================
        elif request.POST.get("new_address"):
            Address.objects.create(
                user=request.user,
                full_name=request.POST.get("full_name"),
                phone=request.POST.get("phone"),
                address_line=request.POST.get("address_line"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                pincode=request.POST.get("pincode"),
            )
            return redirect('checkout')

        # =========================
        # PLACE ORDER
        # =========================
        elif 'payment_method' in request.POST:

            payment_method = request.POST.get('payment_method').lower()
            address_id = request.POST.get('address')

            if not address_id:
                error = "Please select address"

            else:
                address = Address.objects.get(id=address_id, user=request.user)

                total = subtotal - Decimal(request.session.get('discount', "0"))

                order = Order.objects.create(
                    user=request.user,
                    total_amount=total,
                    payment_method=payment_method,
                    address=address,
                    status="pending"
                )

                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        size=item.size,
                        price=item.product.price
                    )

                request.session.pop('coupon', None)
                request.session.pop('discount', None)

                if payment_method == "cod":
                    cart_items.delete()
                    return redirect('order_success', order_id=order.id)

                elif payment_method == "razorpay":
                    try:
                        client = razorpay.Client(
                            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                        )

                        payment = client.order.create({
                            "amount": int(total * 100),
                            "currency": "INR",
                            "payment_capture": 1
                        })

                        order.razorpay_order_id = payment["id"]
                        order.save()

                        return render(request, "razorpay_payment.html", {
                            "order": order,
                            "payment": payment,
                            "key": settings.RAZORPAY_KEY_ID
                        })
                    except Exception as e:
                        logger.exception("Razorpay order creation failed: %s", e)
                        order.delete()
                        error = "Payment gateway authentication failed. Please select Cash on Delivery or configure valid credentials."

    # =========================
    # LOAD SESSION
    # =========================
    if request.session.get('discount'):
        discount = Decimal(request.session.get('discount'))

    coupon_code = request.session.get('coupon')
    total = subtotal - discount
    from django.utils import timezone

    available_coupons = Coupon.objects.filter(
    active=True,
    valid_from__lte=timezone.now(),
    valid_to__gte=timezone.now()
    )

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'addresses': addresses,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'coupon_code': coupon_code,
        'error': error,
        'available_coupons': available_coupons
    })
@login_required
def order_success(request, order_id):

    order = Order.objects.get(id=order_id)

    return render(request,'order_success.html',{
        'order':order
    })

@login_required
def order_history(request):
    orders_list = Order.objects.filter(user=request.user).order_by('-id')

    paginator = Paginator(orders_list, 5)  # 🔥 5 orders per page

    page_number = request.GET.get('page')  # get page number from URL
    orders = paginator.get_page(page_number)

    return render(request, 'order_history.html', {
        'orders': orders
    })

@login_required
def add_to_wishlist(request,product_id):
    """
    Saves a product item to the authenticated user's wishlist.
    """
    product=get_object_or_404(Products,id=product_id)
    item, created = Wishlist.objects.get_or_create(user=request.user,product=product)
    return redirect('wishlist')

@login_required
def wishlist(request):
    """
    Renders the wishlist page showing all saved items for the user.
    """
    items=Wishlist.objects.filter(user=request.user)
    categories=Cateogry.objects.all()
    return render(request,'wishlist.html',{'items':items,'categories':categories})

@login_required
def remove_wishlist(request,product_id):
    """
    Deletes a product item from the authenticated user's wishlist.
    """
    Wishlist.objects.filter(user=request.user,product_id=product_id).delete()
    return redirect('wishlist')


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # 🔥 Allow cancel till shipped
    if order.status in ["pending", "processing", "shipped"]:
        order.status = "cancelled"
        order.save()
        messages.success(request, "Order cancelled successfully")

    return redirect('order_history')

def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        count = Cart.objects.filter(user=request.user).count()
    return {'cart_count': count}


@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    product_sizes = []
    if product.sizes:
        product_sizes = [s.strip() for s in product.sizes.split(',') if s.strip()]

    reviews = product.reviews.all().order_by('-created_at')

    # Calculate average rating
    avg_rating = 0
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()
        avg_rating = round(avg_rating, 1)

    # Check if this user bought this product (Verified Purchase indicator)
    is_verified_buyer = OrderItem.objects.filter(
        order__user=request.user,
        order__payment_status='Success',
        product=product
    ).exists() or OrderItem.objects.filter(
        order__user=request.user,
        order__payment_status='Paid',
        product=product
    ).exists() or OrderItem.objects.filter(
        order__user=request.user,
        order__status='Delivered',
        product=product
    ).exists()

    # Check if the user already submitted a review to prevent multiple reviews
    user_review = reviews.filter(user=request.user).first()

    # Calculate rating breakdown percentages (5 star down to 1 star)
    rating_breakdown = {i: 0 for i in range(1, 6)}
    total_reviews = reviews.count()
    if total_reviews > 0:
        for r in reviews:
            rating_breakdown[r.rating] += 1
        # Convert counts to percentages
        for i in range(1, 6):
            rating_breakdown[i] = round((rating_breakdown[i] / total_reviews) * 100)

    if request.method == 'POST':
        if user_review:
            messages.error(request, "You have already reviewed this product.")
            return redirect('product_detail', product_id=product.id)

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Thank you! Your review has been submitted.")
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReviewForm()

    context = {
        'product': product,
        'product_sizes': product_sizes,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'is_verified_buyer': is_verified_buyer,
        'user_review': user_review,
        'rating_breakdown': rating_breakdown,
        'form': form,
    }
    return render(request, 'product_detail.html', context)



@login_required
def buy_now(request, product_id):

    # Clear previous cart
    Cart.objects.filter(user=request.user).delete()

    product = get_object_or_404(Products, id=product_id)

    quantity = int(request.POST.get('quantity', 1))
    size = request.POST.get('size', 'M')

    # ❌ Prevent invalid quantity
    if quantity < 1:
        quantity = 1

    # ❌ Prevent over stock
    if quantity > product.stock:
        quantity = product.stock

    Cart.objects.create(
        user=request.user,
        product=product,
        quantity=quantity,
        size=size
    )

    return redirect('checkout')


def contact(request):

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        Contact.objects.create(
            name=name,
            email=email,
            message=message
        )

        messages.success(request, "Thank you! Your message has been sent successfully.")
        return redirect("index")

    return render(request, "contact.html")


@login_required
def order_tracking(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)
    return render(request, "order_tracking.html", {"order": order})

def search(request):
    query = request.GET.get('q')

    if query:
        products = Products.objects.filter(name__icontains=query)
    else:
        products = []

    context = {
        'query': query,
        'products': products
    }

    return render(request, 'search.html', context)

def shop(request):
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Products.objects.all()
    categories = Cateogry.objects.all()

    if category_id:
        products = products.filter(category_id=category_id)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    # 🔥 PAGINATION
    paginator = Paginator(products, 10)  
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'shop.html', {
        'products': products,
        'categories': categories
    })
@login_required
def checkout_increase(request, product_id):

    cart_item = Cart.objects.filter(
        user=request.user,
        product_id=product_id
    ).first()

    if cart_item:
        # ✅ prevent exceeding stock
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()

    return redirect('checkout')   # 🔥 important


@login_required
def checkout_decrease(request, product_id):

    cart_item = Cart.objects.filter(
        user=request.user,
        product_id=product_id
    ).first()

    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()

    return redirect('checkout')  

def payment_success(request):
    """
    Handle the successful Razorpay payment callback.
    Updates the order status, reduces product stock levels,
    clears the user's cart, and redirects to the order success page.
    """
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        payment_id = request.POST.get("payment_id")

        # Retrieve and update the order with payment details
        order = Order.objects.get(id=order_id)
        order.razorpay_payment_id = payment_id
        order.payment_status = "Paid"
        order.status = "Processing"
        order.save()

        # Reduce stock for each purchased product item
        items = OrderItem.objects.filter(order=order)
        for item in items:
            item.product.stock -= item.quantity
            item.product.save()

        # Clear the user's shopping cart after successful checkout
        Cart.objects.filter(user=order.user).delete()

        return redirect('order_success', order_id=order.id)