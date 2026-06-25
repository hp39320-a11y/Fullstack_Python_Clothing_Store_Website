from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class AdminPanelDashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.normal_user = User.objects.create_user(username="normaluser", password="password")
        self.staff_user = User.objects.create_user(username="staffuser", password="password", is_staff=True)

    def test_dashboard_blocks_anonymous(self):
        url = reverse('admin_dashboard')
        response = self.client.get(url)
        # Should redirect to login since @login_required is used
        self.assertEqual(response.status_code, 302)
        self.assertTrue('login' in response.url)

    def test_dashboard_blocks_non_staff(self):
        url = reverse('admin_dashboard')
        self.client.login(username="normaluser", password="password")
        response = self.client.get(url)
        # Should redirect to index page because of @admin_required redirect('index')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/')

    def test_dashboard_allows_staff(self):
        url = reverse('admin_dashboard')
        self.client.login(username="staffuser", password="password")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminpanel/dashboard.html')
