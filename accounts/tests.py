from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.profile_url = reverse('accounts:profile')

    def test_profile_view_requires_login(self):
        response = self.client.get(self.profile_url)
        self.assertNotEqual(response.status_code, 200)

    def test_profile_view_get(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('user_form', response.context)
        self.assertIn('profile_form', response.context)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_profile_view_post_update(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.profile_url, {
            'username': 'testuser',
            'first_name': 'NewFirst',
            'last_name': 'NewLast',
            'email': 'new@example.com',
            'bio': 'Test bio',
            'location': 'Test city',
            'birth_date': '1990-01-01',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewFirst')
        self.assertEqual(self.user.profile.bio, 'Test bio')
        self.assertEqual(self.user.profile.location, 'Test city')
        self.assertEqual(str(self.user.profile.birth_date), '1990-01-01')
