from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


class LogoutTests(APITestCase):

    def setUp(self):
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
        self.client.cookies["access_token"] = self.access_token
        self.client.cookies["refresh_token"] = self.refresh_token

    def _assert_cookie_deleted(self, response, name):
        self.assertEqual(response.cookies[name].value, "")
        self.assertEqual(
            str(response.cookies[name]["max-age"]),
            "0",
        )

    def test_logout_succeeds(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "detail": (
                    "Log-Out successfully! All Tokens will be deleted. "
                    "Refresh token is now invalid."
                )
            },
        )
        self._assert_cookie_deleted(response, "access_token")
        self._assert_cookie_deleted(response, "refresh_token")

    def test_logout_fails_without_access_token(self):
        del self.client.cookies["access_token"]

        response = self.client.post(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_access_token_is_invalid_after_logout(self):
        self.client.post(self.url)
        self.client.cookies["access_token"] = self.access_token

        response = self.client.post(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_refresh_token_is_invalid_after_logout(self):
        self.client.post(self.url)
        self.client.cookies["refresh_token"] = self.refresh_token

        response = self.client.post(self.refresh_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_logout_succeeds_with_invalid_refresh_token(self):
        self.client.cookies["refresh_token"] = "invalid-token"

        response = self.client.post(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
