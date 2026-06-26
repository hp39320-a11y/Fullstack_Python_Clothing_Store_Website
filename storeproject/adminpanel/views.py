from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from storeapp.models import (
    Contact,
    Coupon,
    Order,
    Products,
    Cateogry,
    Subcategory,
)


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_login(request):
    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            if user.is_staff:
                login(request, user)
                return redirect('admin_dashboard')
            else:
                return render(request, 'adminpanel/login.html', {
                    'error': 'Not an admin account'
                })
        else:
            return render(request, 'adminpanel/login.html', {
                'error': 'Invalid credentials'
            })

 
    return render(request, 'adminpanel/login.html')

@login_required
def admin_logout(request):
    logout(request)
    return redirect('admin_login') 

    return render(request, 'adminpanel/login.html')
# DASHBOARD
@login_required
@admin_required
def dashboard(request):
    """
    Renders the administrative dashboard showing order, product, and user count statistics.
    """
    return render(request, 'adminpanel/dashboard.html', {
        'orders': Order.objects.count(),
        'products': Products.objects.count(),
        'users': User.objects.count()
    })


# =========================
# PRODUCTS
# =========================

@login_required
@admin_required
def categories(request):
    categories = Cateogry.objects.all()
    return render(request, 'adminpanel/categories.html', {'categories': categories})

@login_required
@admin_required
def add_category(request):
    if request.method == "POST":
        name = request.POST.get('name')
        Cateogry.objects.create(name=name)
        return redirect('admin_categories')

    return render(request, 'adminpanel/add_category.html')


@login_required
@admin_required
def edit_category(request, id):
    category = get_object_or_404(Cateogry, id=id)

    if request.method == "POST":
        category.name = request.POST.get('name')
        category.save()
        return redirect('admin_categories')

    return render(request, 'adminpanel/edit_category.html', {
        'category': category
    })

@login_required
@admin_required
def delete_category(request, id):
    Cateogry.objects.filter(id=id).delete()
    return redirect('admin_categories')

@login_required
@admin_required
def subcategories(request):
    subs = Subcategory.objects.select_related('category')
    return render(request, 'adminpanel/subcategories.html', {'subs': subs})

@login_required
@admin_required
def add_subcategory(request):

    categories = Cateogry.objects.all()

    if request.method == "POST":
        Subcategory.objects.create(
            name=request.POST.get('name'),
            category_id=request.POST.get('category')
        )
        return redirect('admin_subcategories')

    return render(request, 'adminpanel/add_subcategory.html', {
        'categories': categories
    })

@login_required
@admin_required
def edit_subcategory(request, id):
    sub = get_object_or_404(Subcategory, id=id)
    categories = Cateogry.objects.all()

    if request.method == "POST":
        sub.name = request.POST.get('name')
        sub.category_id = request.POST.get('category')
        sub.save()
        return redirect('admin_subcategories')

    return render(request, 'adminpanel/edit_subcategory.html', {
        'sub': sub,
        'categories': categories
    })

@login_required
@admin_required
def delete_subcategory(request, id):
    Subcategory.objects.filter(id=id).delete()
    return redirect('admin_subcategories')


@login_required
@admin_required
def products(request):

    search = request.GET.get('search')
    category = request.GET.get('category')

    products = Products.objects.all()

    if search:
        products = products.filter(name__icontains=search)

    if category:
        products = products.filter(category_id=category)

    categories = Cateogry.objects.all()

    return render(request, 'adminpanel/products.html', {
        'products': products,
        'categories': categories
    })


@login_required
@admin_required
def add_product(request):

    categories = Cateogry.objects.all()
    subs = Subcategory.objects.all()

    if request.method == "POST":
        Products.objects.create(
            name=request.POST.get('name'),
            price=request.POST.get('price'),
            stock=request.POST.get('stock'),
            category_id=request.POST.get('category'),
            subcategory_id=request.POST.get('subcategory'),
            description=request.POST.get('description'),
            sizes=request.POST.get('sizes'),
            image=request.FILES.get('image') or None
        )
        return redirect('admin_products')

    return render(request, 'adminpanel/add_product.html', {
        'categories': categories,
        'subs': subs
    })

@login_required
@admin_required
def edit_product(request, id):

    product = get_object_or_404(Products, id=id)
    categories = Cateogry.objects.all()
    subs = Subcategory.objects.all()

    if request.method == "POST":

        product.name = request.POST.get('name')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')

        product.category_id = request.POST.get('category')
        product.subcategory_id = request.POST.get('subcategory')

        product.description = request.POST.get('description')
        product.sizes = request.POST.get('sizes')

        if request.FILES.get('image'):
            if product.image:
                product.image.delete()
            product.image = request.FILES.get('image')

        product.save()

        return redirect('admin_products')

    return render(request, 'adminpanel/edit_product.html', {
        'product': product,
        'categories': categories,
        'subs': subs
    })

@login_required
@admin_required
def delete_product(request, id):
    Products.objects.filter(id=id).delete()
    return redirect('admin_products')





@login_required
@admin_required
def orders(request):
    orders = Order.objects.all().order_by('-id')  # fetch all orders from DB
    return render(request, 'adminpanel/orders.html', {'orders': orders})

@login_required
@admin_required
def update_order(request, id):
    order = Order.objects.get(id=id)

    if request.method == "POST":
        order.status = request.POST.get('status')
        order.save()

    return redirect('admin_orders')

@login_required
@admin_required
def view_order(request, id):
    order = get_object_or_404(Order, id=id)
    order_items = order.orderitem_set.all()  # fetch all items for this order
    return render(request, 'adminpanel/view_order.html', {
        'order': order,
        'order_items': order_items
    })
@login_required
@admin_required
def contacts(request):
    contacts = Contact.objects.all().order_by('-created_at')
    return render(request, 'adminpanel/contacts.html', {
        'contacts': contacts
    })

@login_required
@admin_required
def coupons(request):
    coupons = Coupon.objects.all().order_by('-id')
    return render(request, 'adminpanel/coupons.html', {
        'coupons': coupons
    })

@login_required
@admin_required
def add_coupon(request):
    if request.method == "POST":
        code = request.POST.get('code')
        discount = request.POST.get('discount')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')
        active = request.POST.get('active') == "on"

        if Coupon.objects.filter(code=code).exists():
            return render(request, 'adminpanel/add_coupon.html', {
                'error': 'Coupon code already exists.'
            })

        Coupon.objects.create(
            code=code,
            discount=discount,
            valid_from=valid_from,
            valid_to=valid_to,
            active=active
        )
        return redirect('admin_coupons')

    return render(request, 'adminpanel/add_coupon.html')


@login_required
@admin_required
def delete_coupon(request, id):
    Coupon.objects.filter(id=id).delete()
    return redirect('admin_coupons')