from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Cateogry, Subcategory, Products, Cart, Coupon, Address

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

class CouponModelTest(TestCase):
    def setUp(self):
        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code="SUMMER20",
            discount=20,
            active=True,
            valid_from=now - timedelta(days=1),
            valid_to=now + timedelta(days=5)
        )

    def test_coupon_creation(self):
        self.assertEqual(self.coupon.code, "SUMMER20")
        self.assertEqual(self.coupon.discount, 20)
        self.assertTrue(self.coupon.active)
        self.assertEqual(str(self.coupon), "SUMMER20")

class CartCountContextProcessorTest(TestCase):
    def setUp(self):
        from django.test import RequestFactory
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="cartuser", password="password")
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

    def test_cart_count_anonymous(self):
        from django.contrib.auth.models import AnonymousUser
        from .context_processors import cart_count
        request = self.factory.get('/')
        request.user = AnonymousUser()
        result = cart_count(request)
        self.assertEqual(result['cart_count'], 0)

    def test_cart_count_authenticated(self):
        from .context_processors import cart_count
        request = self.factory.get('/')
        request.user = self.user
        result = cart_count(request)
        self.assertEqual(result['cart_count'], 0)

        Cart.objects.create(user=self.user, product=self.product, quantity=1)
        result = cart_count(request)
        self.assertEqual(result['cart_count'], 1)

class RoleBasedAccessMiddlewareTest(TestCase):
    def setUp(self):
        from django.test import RequestFactory
        from django.http import HttpResponse
        self.factory = RequestFactory()
        self.get_response = lambda req: HttpResponse("success")
        self.user = User.objects.create_user(username="normaluser", password="password")
        self.staff_user = User.objects.create_user(username="staffuser", password="password", is_staff=True)

    def test_middleware_blocks_non_staff_from_admin(self):
        from .middleware import RoleBasedAccessMiddleware
        middleware = RoleBasedAccessMiddleware(self.get_response)
        request = self.factory.get('/admin-panel/')
        request.user = self.user
        response = middleware(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_middleware_allows_staff_to_admin(self):
        from .middleware import RoleBasedAccessMiddleware
        middleware = RoleBasedAccessMiddleware(self.get_response)
        request = self.factory.get('/admin-panel/')
        request.user = self.staff_user
        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"success")


class AddressModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="addressuser", password="password")
        self.address = Address.objects.create(
            user=self.user,
            full_name="John Doe",
            phone="1234567890",
            address_line="123 Street Name",
            city="Chennai",
            state="Tamil Nadu",
            pincode="600001"
        )

    def test_address_creation(self):
        self.assertEqual(self.address.user, self.user)
        self.assertEqual(self.address.full_name, "John Doe")
        self.assertEqual(self.address.phone, "1234567890")
        self.assertEqual(self.address.address_line, "123 Street Name")
        self.assertEqual(self.address.city, "Chennai")
        self.assertEqual(self.address.state, "Tamil Nadu")
        self.assertEqual(self.address.pincode, "600001")
        self.assertEqual(str(self.address), "John Doe")
