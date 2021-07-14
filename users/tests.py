from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
import requests


class UserLoginTestCase(TestCase):

    def setUp(self) -> None:
        self.login_requirements = {
            'username': 'ghasem',
            'password': '12345678910',
        }
        self.user = get_user_model().objects.create_user(**self.login_requirements, is_superuser=True)

    def test_a_urls_before_login(self):

        # TODO: why 302 instead of 403 ?

        # response = self.client.post(reverse("info:update")) # -> 302
        response = requests.post('http://127.0.0.1:8000/info/update/') # -> 403
        self.assertEqual(response.status_code, 403)

        response = requests.get('http://127.0.0.1:8000/info/update/')
        self.assertEqual(response.status_code, 405)

        response = self.client.get(reverse("info:update"))
        self.assert_(response.status_code, 405)

        response = self.client.get(reverse("user:login"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("home:home"))
        self.assertTrue(True if not response.wsgi_request.user.is_authenticated else False)

        response = self.client.get(reverse("home:activities"))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse("info:add_info"))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse("info:search"))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse("info:show_info"))
        self.assertEqual(response.status_code, 302)

    def test_b_check_user_login_unsuccessfully(self):
        login_requirements = {
            'username': 'mostafa',
            'password': '123234'
        }
        response = self.client.post(reverse('user:login'), data=login_requirements)
        self.assertEqual(response.status_code, 200)

    def test_c_check_user_login_successfully(self):
        _response = self.client.post(reverse('user:login'), data=self.login_requirements)
        self.assertEqual(_response.status_code, 302)

    def test_d_urls_after_login(self):
        self.client.post(reverse('user:login'), data=self.login_requirements)  # login user

        response = self.client.get(reverse("home:home"))
        self.assertFalse(True if not response.wsgi_request.user.is_authenticated else False)

        response = self.client.get(reverse("home:activities"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("info:add_info"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("info:search"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("info:show_info"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("info:update"))
        self.assertEqual(response.status_code, 405)

        response = self.client.post(reverse("info:update"))
        self.assertEqual(response.status_code, 404)


class UserLogoutTestCase(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='ghasem', password='12345678910')

    def test_a_logout_url(self):
        response = self.client.get(reverse("user:logout"))
        self.assertEqual(response.status_code, 302)

    def test_b_user_logout(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse("user:logout"))
        session = response.client.cookies['sessionid']
        self.assertFalse(session['httponly'], False)
