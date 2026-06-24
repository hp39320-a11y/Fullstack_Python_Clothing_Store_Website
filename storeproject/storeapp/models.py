from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Cateogry(models.Model):
    """
    Model representing a parent product category (e.g. Men's wear, Women's wear).
    """
    name=models.CharField(max_length=100)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Subcategory(models.Model):
    """
    Model representing a subcategory under a parent category (e.g. T-shirts under Men's).
    """
    category=models.ForeignKey(Cateogry,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    image = models.ImageField(upload_to='subcategory/', null=True, blank=True)

    created_at=models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Products(models.Model):
    """
    Model representing an individual clothing item/product with stock management.
    """
    category = models.ForeignKey(Cateogry, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    image = models.ImageField(upload_to='products/')
    description = models.TextField(blank=True, null=True)
    sizes = models.CharField(
        max_length=100,
        blank=True,
        help_text="Comma-separated sizes e.g., S,M,L,XL"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Cart(models.Model):
    """
    Model representing an item added to the user's shopping cart.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=5, default='M',blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.product.price * self.quantity


class Wishlist(models.Model):
    """
    Model representing a product saved in the user's personal wishlist.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product.name


STATUS_CHOICES = (
    ('Pending', 'Pending'),
    ('Processing', 'Processing'),
    ('Shipped', 'Shipped'),
    ('Out for Delivery', 'Out for Delivery'),
    ('Delivered', 'Delivered'),
    ('Cancelled','Cancelled'),
)

class Address(models.Model):
    """
    Model representing a shipping address saved by the customer for checkout.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

class Order(models.Model):
    """
    Model representing a customer order containing items and payment status.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    PAYMENT_STATUS = (
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    )

    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="Pending")

    razorpay_order_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=200, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=200, null=True, blank=True)

    status = models.CharField(max_length=70, choices=STATUS_CHOICES, default='Pending')
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)

    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    """
    Model representing a specific product line item purchased within an order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=5, default='M')
    created_at = models.DateTimeField(auto_now_add=True) 
    def __str__(self):
        return f"Order {self.id}"

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount = models.IntegerField(help_text="Percentage (e.g. 10 for 10%)")
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return self.code
    


    
    
