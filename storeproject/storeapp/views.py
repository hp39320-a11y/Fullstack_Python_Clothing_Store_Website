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
        
        size = 'M'
        quantity = 1
        
        # Try to parse from JSON first
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                size = data.get('size', 'M')
                quantity = int(data.get('quantity', 1))
            except Exception:
                pass
        else:
            # Parse from POST fields
            size = request.POST.get('size', 'M')
            try:
                quantity = int(request.POST.get('quantity', 1))
            except (ValueError, TypeError):
                quantity = 1

        if not size:
            size = 'M'
        if quantity < 1:
            quantity = 1

        # Check if the product has size options, validate choice
        if product.sizes:
            valid_sizes = [s.strip() for s in product.sizes.split(',') if s.strip()]
            if valid_sizes and size not in valid_sizes:
                size = valid_sizes[0]

        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            size=size,
            defaults={'quantity': quantity}
        )

        if not created:
            if cart_item.quantity + quantity <= product.stock:
                cart_item.quantity += quantity
            else:
                cart_item.quantity = product.stock
            cart_item.save()

        # Return updated count of items in the cart
        total_cart_count = sum(item.quantity for item in Cart.objects.filter(user=request.user))
        return JsonResponse({
            "status": "success",
            "cart_count": total_cart_count
        })

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


@login_required
def api_cart_update(request, item_id):
    if request.method == "POST":
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        action = request.POST.get('action')
        
        status = "success"
        message = ""
        
        if action == 'increase':
            if cart_item.quantity < cart_item.product.stock:
                cart_item.quantity += 1
                cart_item.save()
            else:
                status = "error"
                message = "Stock limit reached!"
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                status = "removed"
                message = "Item removed"
        elif action == 'set':
            try:
                qty = int(request.POST.get('quantity', 1))
                if qty < 1:
                    cart_item.delete()
                    status = "removed"
                    message = "Item removed"
                else:
                    if qty <= cart_item.product.stock:
                        cart_item.quantity = qty
                        cart_item.save()
                    else:
                        cart_item.quantity = cart_item.product.stock
                        cart_item.save()
                        status = "error"
                        message = f"Only {cart_item.product.stock} units available!"
            except Exception:
                status = "error"
                message = "Invalid quantity"
        else:
            status = "error"
            message = "Invalid action"

        # Calculate new totals
        cart_items = Cart.objects.filter(user=request.user)
        total = sum(item.total_price() for item in cart_items)
        cart_count = sum(item.quantity for item in cart_items)
        
        delivery = 0 if (total >= 999 or total == 0) else 79
        grand_total = total + delivery

        return JsonResponse({
            "status": status,
            "message": message,
            "quantity": cart_item.quantity if (status == "success" or status == "error") else 0,
            "item_total_price": float(cart_item.total_price()) if (status == "success" or status == "error") else 0,
            "subtotal": float(total),
            "cart_count": cart_count,
            "delivery": delivery,
            "grand_total": float(grand_total)
        })
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


@login_required
def api_cart_remove(request, item_id):
    if request.method == "POST":
        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        cart_item.delete()
        
        cart_items = Cart.objects.filter(user=request.user)
        total = sum(item.total_price() for item in cart_items)
        cart_count = sum(item.quantity for item in cart_items)
        
        delivery = 0 if (total >= 999 or total == 0) else 79
        grand_total = total + delivery

        return JsonResponse({
            "status": "success",
            "message": "Item removed successfully",
            "subtotal": float(total),
            "cart_count": cart_count,
            "delivery": delivery,
            "grand_total": float(grand_total)
        })
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=400)


@login_required
def cart_detail(request):
    """
    Renders the cart details page showing items, quantities, and subtotal.
    """
    cart_items = Cart.objects.filter(user=request.user)

    total = sum(item.total_price() for item in cart_items)
    delivery_fee = 0 if (total >= 999 or total == 0) else 79
    grand_total = total + delivery_fee

    categories = Cateogry.objects.all()

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total': total,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
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

                if coupon.is_valid(subtotal):
                    discount = (Decimal(coupon.discount) / Decimal("100")) * subtotal

                    request.session['coupon'] = coupon.code
                    request.session['discount'] = str(discount)

                    return redirect('checkout')
                else:
                    if coupon.min_purchase_amount > subtotal:
                        error = f"Minimum purchase of ₹{coupon.min_purchase_amount} required for this coupon"
                    else:
                        error = "Coupon is invalid or expired"

            except Coupon.DoesNotExist:
                error = "Invalid coupon"

        # =========================
        # REMOVE COUPON
        # =========================
        elif 'remove_coupon' in request.POST:
            request.session.pop('coupon', None)
            request.session.pop('discount', None)
            return redirect('checkout')

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

                # Validate coupon from session again
                saved_coupon_code = request.session.get('coupon')
                if saved_coupon_code:
                    try:
                        coupon = Coupon.objects.get(code=saved_coupon_code, active=True)
                        if coupon.is_valid(subtotal):
                            discount = (Decimal(coupon.discount) / Decimal("100")) * subtotal
                        else:
                            discount = Decimal("0")
                            request.session.pop('coupon', None)
                            request.session.pop('discount', None)
                    except Coupon.DoesNotExist:
                        discount = Decimal("0")
                        request.session.pop('coupon', None)
                        request.session.pop('discount', None)

                # Correctly calculate total: subtotal - discount + shipping_fee
                shipping_fee = Decimal("0") if (subtotal >= 999 or subtotal == 0) else Decimal("79")
                total = subtotal - discount + shipping_fee

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
    coupon_code = request.session.get('coupon')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, active=True)
            if coupon.is_valid(subtotal):
                discount = (Decimal(coupon.discount) / Decimal("100")) * subtotal
                request.session['discount'] = str(discount)
            else:
                request.session.pop('coupon', None)
                request.session.pop('discount', None)
                discount = Decimal("0")
                coupon_code = None
                error = f"Coupon {coupon.code} removed because minimum order requirement of ₹{coupon.min_purchase_amount} was not met."
        except Coupon.DoesNotExist:
            request.session.pop('coupon', None)
            request.session.pop('discount', None)
            discount = Decimal("0")
            coupon_code = None

    shipping_fee = Decimal("0") if (subtotal >= 999 or subtotal == 0) else Decimal("79")
    total = subtotal - discount + shipping_fee
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
        'shipping_fee': shipping_fee,
        'total': total,
        'coupon_code': coupon_code,
        'error': error,
        'available_coupons': available_coupons
    })


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == "POST":
        address.delete()
        return JsonResponse({"status": "success", "message": "Address deleted successfully"})
    return JsonResponse({"status": "error", "message": "Invalid method"}, status=400)
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
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort_by', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    if query:
        products = Products.objects.filter(name__icontains=query)
    else:
        products = Products.objects.none()

    if category_id:
        products = products.filter(category_id=category_id)

    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except Exception:
            pass

    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')

    categories = Cateogry.objects.all()

    context = {
        'query': query,
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'selected_sort': sort_by,
        'min_price': min_price,
        'max_price': max_price
    }

    return render(request, 'search.html', context)


def search_suggestions(request):
    query = request.GET.get('q', '').strip()
    results = []
    if len(query) >= 2:
        products = Products.objects.filter(name__icontains=query)[:5]
        for p in products:
            image_url = p.image.url if p.image else ""
            results.append({
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "image_url": image_url
            })
    return JsonResponse({"results": results})

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