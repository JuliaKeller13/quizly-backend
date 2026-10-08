from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


User = get_user_model()


class LoginTests(APITestCase):
    """Tests the login endpoint."""

    def setUp(self):
        """Creates a user for login tests."""
        self.url = "/api/login/"
        self.password = "ExamplePassword123!"
        self.user = User.objects.create_user(
            username="exampleUsername",
            email="example@mail.de",
            password=self.password,
        )

    def _login(self, username, password):
        """Sends a login request."""
        return self.client.post(
            self.url,
            {"username": username, "password": password},
            format="json",
        )

    def _expected_login_data(self):
        """Returns the expected successful login response."""
        return {
            "detail": "Login successfully!",
            "user": {
                "id": self.user.id,
                "username": self.user.username,
                "email": self.user.email,
            },
        }

    def _assert_auth_cookies(self, response):
        """Checks both authentication cookies."""
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)
        self.assertTrue(response.cookies["access_token"]["httponly"])
        self.assertTrue(response.cookies["refresh_token"]["httponly"])
        AccessToken(response.cookies["access_token"].value)
        RefreshToken(response.cookies["refresh_token"].value)

    def _assert_invalid_login(self, response):
        """Checks a rejected login response."""
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data, {"detail": "Invalid credentials."})

    def test_login_succeeds_with_valid_credentials(self):
        """Logs in with valid credentials."""
        response = self._login(self.user.username, self.password)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self._expected_login_data())
        self._assert_auth_cookies(response)

    def test_login_fails_with_wrong_password(self):
        """Rejects an incorrect password."""
        response = self._login(
            self.user.username,
            "WrongPassword123!",
        )

        self._assert_invalid_login(response)

    def test_login_fails_with_unknown_username(self):
        """Rejects an unknown username."""
        response = self._login("unknownUser", self.password)

        self._assert_invalid_login(response)
