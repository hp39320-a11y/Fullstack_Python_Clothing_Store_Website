from django.test import TestCase
from .models import Cateogry, Subcategory

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
