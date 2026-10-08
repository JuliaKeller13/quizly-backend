from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class RegistrationTests(APITestCase):
    """Tests the registration endpoint."""

    def setUp(self):
        """Creates valid registration data."""
        self.url = "/api/register/"
        self.data = {
            "username": "exampleUsername",
            "password": "ExamplePassword123!",
            "confirmed_password": "ExamplePassword123!",
            "email": "example@mail.de",
        }

    def _post_registration(self):
        """Sends the current registration data."""
        return self.client.post(
            self.url,
            self.data,
            format="json",
        )

    def _create_user(self, username, email):
        """Creates an existing user for duplicate tests."""
        return User.objects.create_user(
            username=username,
            email=email,
            password="ExistingPassword123!",
        )

    def _assert_bad_request(self, response):
        """Checks a rejected registration response."""
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def _assert_password_is_hashed(self, user):
        """Checks that the stored password is hashed and valid."""
        self.assertNotEqual(user.password, self.data["password"])
        self.assertTrue(user.check_password(self.data["password"]))

    def test_registration_creates_user_successfully(self):
        """Creates a user from valid registration data."""
        response = self._post_registration()
        user = User.objects.get(username=self.data["username"])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data,
            {"detail": "User created successfully!"},
        )
        self._assert_password_is_hashed(user)

    def test_registration_fails_when_passwords_differ(self):
        """Rejects mismatching password fields."""
        self.data["confirmed_password"] = "DifferentPassword123!"

        response = self._post_registration()

        self._assert_bad_request(response)
        self.assertFalse(
            User.objects.filter(username=self.data["username"]).exists()
        )

    def test_registration_fails_with_existing_username(self):
        """Rejects an existing username."""
        self._create_user(self.data["username"], "different@mail.de")

        response = self._post_registration()

        self._assert_bad_request(response)

    def test_registration_fails_with_existing_email(self):
        """Rejects an email address that is already registered."""
        self._create_user("differentUsername", self.data["email"])

        response = self._post_registration()

        self._assert_bad_request(response)
        self.assertIn("email", response.data)

    def test_registration_fails_with_missing_username(self):
        """Rejects registration without a username."""
        self.data.pop("username")

        response = self._post_registration()

        self._assert_bad_request(response)

    def test_registration_fails_without_email(self):
        """Ensures that email is required."""
        self.data.pop("email")

        response = self._post_registration()

        self._assert_bad_request(response)

    def test_registration_fails_with_blank_email(self):
        """Ensures that email cannot be blank."""
        self.data["email"] = ""

        response = self._post_registration()

        self._assert_bad_request(response)

    def test_registration_fails_with_short_username(self):
        """Ensures that usernames contain at least three characters."""
        self.data["username"] = "ab"

        response = self._post_registration()

        self._assert_bad_request(response)

    def test_registration_fails_with_weak_password(self):
        """Ensures that passwords meet Quizly's requirements."""
        self.data["password"] = "lowercase123"
        self.data["confirmed_password"] = "lowercase123"

        response = self._post_registration()

        self._assert_bad_request(response)
