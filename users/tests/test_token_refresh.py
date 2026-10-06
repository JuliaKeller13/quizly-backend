from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


User = get_user_model()


class TokenRefreshTests(APITestCase):

    def setUp(self):
        self.url = "/api/token/refresh/"
        self.user = User.objects.create_user(
            username="exampleUsername",
            email="example@mail.de",
            password="ExamplePassword123!",
        )

    def test_refresh_creates_new_access_token(self):
        refresh_token = RefreshToken.for_user(self.user)
        self.client.cookies["refresh_token"] = str(refresh_token)

        response = self.client.post(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data,
            {"detail": "Token refreshed"},
        )
        self.assertIn("access_token", response.cookies)
        self.assertTrue(
            response.cookies["access_token"]["httponly"]
        )
        AccessToken(response.cookies["access_token"].value)

    def test_refresh_fails_without_refresh_token(self):
        response = self.client.post(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_refresh_fails_with_invalid_refresh_token(self):
        self.client.cookies["refresh_token"] = "invalid-token"

        response = self.client.post(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )