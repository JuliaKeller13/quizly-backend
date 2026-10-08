from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class LogoutTests(APITestCase):
    """Tests the logout endpoint."""

    def setUp(self):
        """Creates an authenticated user for logout tests."""
        self.url = "/api/logout/"
        self.refresh_url = "/api/token/refresh/"
        self.user = User.objects.create_user(
            username="exampleUsername",
            email="example@mail.de",
            password="ExamplePassword123!",
        )
        refresh_token = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh_token)
        self.access_token = str(refresh_token.access_token)
        self._set_auth_cookies()

    def _set_auth_cookies(self):
        """Sets access and refresh token cookies."""
        self.client.cookies["access_token"] = self.access_token
        self.client.cookies["refresh_token"] = self.refresh_token

    def _assert_cookie_deleted(self, response, name):
        """Checks that one authentication cookie was deleted."""
        self.assertEqual(response.cookies[name].value, "")
        self.assertEqual(str(response.cookies[name]["max-age"]), "0")

    def _expected_logout_data(self):
        """Returns the expected successful logout response."""
        return {
            "detail": (
                "Log-Out successfully! All Tokens will be deleted. "
                "Refresh token is now invalid."
            )
        }

    def test_logout_succeeds(self):
        """Logs out an authenticated user."""
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self._expected_logout_data())
        self._assert_cookie_deleted(response, "access_token")
        self._assert_cookie_deleted(response, "refresh_token")

    def test_logout_fails_without_access_token(self):
        """Rejects logout without an access token."""
        del self.client.cookies["access_token"]

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_token_is_invalid_after_logout(self):
        """Rejects a blacklisted access token after logout."""
        self.client.post(self.url)
        self.client.cookies["access_token"] = self.access_token

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_is_invalid_after_logout(self):
        """Rejects a blacklisted refresh token after logout."""
        self.client.post(self.url)
        self.client.cookies["refresh_token"] = self.refresh_token

        response = self.client.post(self.refresh_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_succeeds_with_invalid_refresh_token(self):
        """Logs out even when the refresh token is already invalid."""
        self.client.cookies["refresh_token"] = "invalid-token"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
