from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class RegistrationTests(APITestCase):

    def setUp(self):
        self.url = "/api/register/"
        self.data = {
            "username": "exampleUsername",
            "password": "ExamplePassword123!",
            "confirmed_password": "ExamplePassword123!",
            "email": "example@mail.de",
        }

    def test_registration_creates_user_successfully(self):
        response = self.client.post(
            self.url,
            self.data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            response.data,
            {"detail": "User created successfully!"},
        )

        user = User.objects.get(
            username=self.data["username"]
        )

        self.assertNotEqual(
            user.password,
            self.data["password"],
        )
        self.assertTrue(
            user.check_password(self.data["password"])
        )

    def test_registration_fails_when_passwords_differ(self):
        self.data["confirmed_password"] = "DifferentPassword123!"

        response = self.client.post(
            self.url,
            self.data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertFalse(
            User.objects.filter(
                username=self.data["username"]
            ).exists()
        )

    def test_registration_fails_with_existing_username(self):
        User.objects.create_user(
            username=self.data["username"],
            email="different@mail.de",
            password="ExistingPassword123!",
        )

        response = self.client.post(
            self.url,
            self.data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_registration_fails_with_existing_email(self):
        User.objects.create_user(
            username="differentUsername",
            email=self.data["email"],
            password="ExistingPassword123!",
        )

        response = self.client.post(
            self.url,
            self.data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_registration_fails_with_missing_username(self):
        self.data.pop("username")

        response = self.client.post(
            self.url,
            self.data,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )