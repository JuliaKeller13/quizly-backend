from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


User = get_user_model()


class LoginTests(APITestCase):

    def setUp(self):
        self.url = "/api/login/"
        self.password = "ExamplePassword123!"
        self.user = User.objects.create_user(
            username="exampleUsername",
            email="example@mail.de",
            password=self.password,
        )

    def _login(self, username, password):
        return self.client.post(
            self.url,
            {
                "username": username,
                "password": password,
            },
            format="json",
        )

    def _assert_auth_cookies(self, response):
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])
        AccessToken(response.cookies["access_token"].value)
        RefreshToken(response.cookies["refresh_token"].value)

    def test_login_succeeds_with_valid_credentials(self):
        response = self._login(
            self.user.username,
            self.password,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "detail": "Login successfully!",
                "user": {
                    "id": self.user.id,
                    "username": self.user.username,
                    "email": self.user.email,
                },
            },
        )
        self._assert_auth_cookies(response)

    def test_login_fails_with_wrong_password(self):
        response = self._login(
            self.user.username,
            "WrongPassword123!",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            response.data,
            {"detail": "Invalid credentials."},
        )

    def test_login_fails_with_unknown_username(self):
        response = self._login(
            "unknownUser",
            self.password,
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            response.data,
            {"detail": "Invalid credentials."},
        )