from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Cateogry, Subcategory, Products, Cart, Coupon, Address, Wishlist, Order, OrderItem, Contact, Review

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

    def test_coupon_is_valid_active_in_range(self):
        self.assertTrue(self.coupon.is_valid())

    def test_coupon_is_valid_inactive(self):
        self.coupon.active = False
        self.coupon.save()
        self.assertFalse(self.coupon.is_valid())

    def test_coupon_is_valid_expired(self):
        now = timezone.now()
        self.coupon.valid_from = now - timedelta(days=5)
        self.coupon.valid_to = now - timedelta(days=1)
        self.coupon.save()
        self.assertFalse(self.coupon.is_valid())

    def test_coupon_is_valid_future(self):
        now = timezone.now()
        self.coupon.valid_from = now + timedelta(days=1)
        self.coupon.valid_to = now + timedelta(days=5)
        self.coupon.save()
        self.assertFalse(self.coupon.is_valid())

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

    def test_get_full_address(self):
        self.assertEqual(
            self.address.get_full_address(),
            "John Doe, 123 Street Name, Chennai, Tamil Nadu - 600001"
        )


class WishlistModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="wishlistuser", password="password")
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
        self.wishlist_item = Wishlist.objects.create(user=self.user, product=self.product)

    def test_wishlist_creation(self):
        self.assertEqual(self.wishlist_item.user, self.user)
        self.assertEqual(self.wishlist_item.product, self.product)
        self.assertEqual(str(self.wishlist_item), "Classic T-Shirt")


class OrderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="orderuser", password="password")
        self.address = Address.objects.create(
            user=self.user,
            full_name="Jane Doe",
            phone="0987654321",
            address_line="456 Avenue",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001"
        )
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
        self.order = Order.objects.create(
            user=self.user,
            total_amount=998.00,
            payment_method="UPI",
            payment_status="Pending",
            address=self.address
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=499.00,
            size="M"
        )

    def test_order_creation(self):
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.total_amount, 998.00)
        self.assertEqual(self.order.payment_method, "UPI")
        self.assertEqual(self.order.payment_status, "Pending")
        self.assertFalse(self.order.is_paid)

    def test_order_item_creation(self):
        self.assertEqual(self.order_item.order, self.order)
        self.assertEqual(self.order_item.product, self.product)
        self.assertEqual(self.order_item.quantity, 2)
        self.assertEqual(self.order_item.price, 499.00)
        self.assertEqual(str(self.order_item), f"Order {self.order.id}")

    def test_get_total_items(self):
        self.assertEqual(self.order.get_total_items, 2)


class ContactModelTest(TestCase):
    def setUp(self):
        self.contact = Contact.objects.create(
            name="Alice Smith",
            email="alice@example.com",
            message="Hello, I have a query about shipping."
        )

    def test_contact_creation(self):
        self.assertEqual(self.contact.name, "Alice Smith")
        self.assertEqual(self.contact.email, "alice@example.com")
        self.assertEqual(self.contact.message, "Hello, I have a query about shipping.")
        self.assertEqual(str(self.contact), "Alice Smith")


class CurrencyFilterTest(TestCase):
    def test_currency_filter_with_valid_numbers(self):
        from .templatetags.custom_filters import currency
        self.assertEqual(currency(1234.56), "₹1,234.56")
        self.assertEqual(currency(100), "₹100.00")
        self.assertEqual(currency("500"), "₹500.00")

    def test_currency_filter_with_invalid_input(self):
        from .templatetags.custom_filters import currency
        self.assertEqual(currency("invalid"), "invalid")
        self.assertEqual(currency(None), None)


class ReviewModelAndViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reviewer", password="password")
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
        self.client.login(username="reviewer", password="password")

    def test_review_creation_and_attributes(self):
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Awesome product",
            comment="Fits perfectly!"
        )
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, "Awesome product")
        self.assertEqual(review.comment, "Fits perfectly!")
        self.assertEqual(str(review), "reviewer's review for Classic T-Shirt")

    def test_review_is_verified_property(self):
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            title="Good",
            comment="Nice buy."
        )
        # Not verified yet
        self.assertFalse(review.is_verified)

        # Create address and order
        address = Address.objects.create(
            user=self.user,
            full_name="Reviewer User",
            phone="1234567890",
            address_line="Street 1",
            city="Chennai",
            state="TN",
            pincode="600001"
        )
        order = Order.objects.create(
            user=self.user,
            total_amount=499.00,
            payment_method="COD",
            payment_status="Success",
            address=address
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=499.00,
            size="M"
        )

        # Now verified since user has purchased product
        self.assertTrue(review.is_verified)

    def test_product_detail_view_context_with_reviews(self):
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            title="Great",
            comment="Love it!"
        )
        # Add another user review
        other_user = User.objects.create_user(username="otheruser", password="password")
        Review.objects.create(
            product=self.product,
            user=other_user,
            rating=3,
            title="Average",
            comment="Okayish"
        )

        response = self.client.get(f"/product/{self.product.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['avg_rating'], 4.0)
        self.assertEqual(response.context['reviews'].count(), 2)
        # 5 star and 3 star are each 50%
        self.assertEqual(response.context['rating_breakdown'][5], 50)
        self.assertEqual(response.context['rating_breakdown'][3], 50)
        self.assertEqual(response.context['rating_breakdown'][4], 0)

    def test_submit_review_post_request(self):
        # Submit a review post request
        response = self.client.post(
            f"/product/{self.product.id}/",
            {"rating": 5, "title": "Excellent", "comment": "Highly recommended!"}
        )
        self.assertRedirects(response, f"/product/{self.product.id}/")
        
        # Verify review created in database
        review = Review.objects.get(product=self.product, user=self.user)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.title, "Excellent")
        self.assertEqual(review.comment, "Highly recommended!")

        # Try submitting another review for the same product (should be blocked)
        response2 = self.client.post(
            f"/product/{self.product.id}/",
            {"rating": 4, "title": "Good second review", "comment": "Changed mind."}
        )
        # The view redirects back to product page but doesn't create a new review
        self.assertEqual(Review.objects.filter(product=self.product, user=self.user).count(), 1)


class EnhancedFeaturesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="enhanceduser", password="password")
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
        self.client.login(username="enhanceduser", password="password")

    def test_coupon_minimum_purchase_validation(self):
        from django.utils import timezone
        from datetime import timedelta
        # Create a coupon requiring ₹1000 minimum purchase
        coupon = Coupon.objects.create(
            code="MIN1000",
            discount=10,
            min_purchase_amount=1000.00,
            active=True,
            valid_from=timezone.now() - timedelta(days=1),
            valid_to=timezone.now() + timedelta(days=5)
        )
        
        # Cart subtotal is 499.00 (less than 1000)
        Cart.objects.create(user=self.user, product=self.product, quantity=1, size="M")
        
        # Apply coupon via POST
        response = self.client.post(
            "/checkout/",
            {"apply_coupon": "MIN1000"}
        )
        # Should render back with error message
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Minimum purchase of")
        # Check that coupon is NOT stored in session discount
        self.assertIsNone(self.client.session.get('coupon'))

    def test_add_to_cart_custom_size_and_quantity(self):
        # Post request to add_to_cart with size 'L' and quantity 2
        response = self.client.post(
            f"/cart/add/{self.product.id}/",
            {"size": "L", "quantity": 2}
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify Cart item exists with chosen size/qty
        cart_item = Cart.objects.get(user=self.user, product=self.product)
        self.assertEqual(cart_item.size, "L")
        self.assertEqual(cart_item.quantity, 2)

    def test_shipping_fee_applied_under_999(self):
        # Create address
        address = Address.objects.create(
            user=self.user,
            full_name="John Doe",
            phone="1234567890",
            address_line="123 Street",
            city="Chennai",
            state="TN",
            pincode="600001"
        )
        # Subtotal = 499.00
        Cart.objects.create(user=self.user, product=self.product, quantity=1, size="M")
        
        # Place COD order
        response = self.client.post(
            "/checkout/",
            {"address": address.id, "payment_method": "COD"}
        )
        self.assertEqual(response.status_code, 302)
        
        # Total should be subtotal + shipping (499.00 + 79.00 = 578.00)
        order = Order.objects.latest('id')
        self.assertEqual(float(order.total_amount), 578.00)

    def test_address_deletion(self):
        address = Address.objects.create(
            user=self.user,
            full_name="Temp Address",
            phone="1234567890",
            address_line="123 Street",
            city="Chennai",
            state="TN",
            pincode="600001"
        )
        response = self.client.post(f"/address/delete/{address.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Address.objects.filter(id=address.id).exists())

