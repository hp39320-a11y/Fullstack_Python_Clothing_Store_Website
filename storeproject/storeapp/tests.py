from django.test import TestCase
from django.contrib.auth.models import User
from .models import Cateogry, Subcategory, Products, Cart

class CategorySubcategoryModelTest(TestCase):
    def setUp(self):
        self.category = Cateogry.objects.create(name="Men's Wear")
        self.subcategory = Subcategory.objects.create(category=self.category, name="T-Shirts")

    def test_category_creation(self):
        self.assertEqual(self.category.name, "Men's Wear")
        self.assertEqual(str(self.category), "Men's Wear")

    def test_subcategory_creation(self):
        self.assertEqual(self.subcategory.name, "T-Shirts")
        self.assertEqual(self.subcategory.category, self.category)
        self.assertEqual(str(self.subcategory), "Men's Wear - T-Shirts")

class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Cateogry.objects.create(name="Men's Wear")
        self.subcategory = Subcategory.objects.create(category=self.category, name="T-Shirts")
        self.product = Products.objects.create(
            category=self.category,
            subcategory=self.subcategory,
            name="Classic T-Shirt",
            price=499.00,
            stock=10,
            image="products/tshirt.jpg"
        )
        self.cart_item = Cart.objects.create(user=self.user, product=self.product, quantity=2, size="L")

    def test_cart_item_creation(self):
        self.assertEqual(self.cart_item.user, self.user)
        self.assertEqual(self.cart_item.product, self.product)
        self.assertEqual(self.cart_item.quantity, 2)
        self.assertEqual(self.cart_item.size, "L")

    def test_cart_total_price(self):
        self.assertEqual(self.cart_item.total_price(), 998.00)

