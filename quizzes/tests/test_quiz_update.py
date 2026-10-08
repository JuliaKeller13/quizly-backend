from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from quizzes.models import Quiz


User = get_user_model()


class QuizUpdateTests(APITestCase):
    """Tests the quiz update endpoint."""

    def setUp(self):
        self.user = self._create_user("owner")
        self.other_user = self._create_user("other")
        self.quiz = self._create_quiz(self.user, "Old Title")
        self.foreign_quiz = self._create_quiz(
            self.other_user,
            "Foreign Quiz",
        )
        self._authenticate()

    def _create_user(self, username):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="ExamplePassword123!",
        )

    def _create_quiz(self, user, title):
        return Quiz.objects.create(
            user=user,
            title=title,
            description="Old Description",
            video_url="https://www.youtube.com/watch?v=example",
        )

    def _authenticate(self):
        refresh_token = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(
            refresh_token.access_token
        )

    def test_patch_updates_title(self):
        response = self.client.patch(
            f"/api/quizzes/{self.quiz.id}/",
            {"title": "Updated Title"},
            format="json",
        )

        self.quiz.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.quiz.title, "Updated Title")
        self.assertEqual(self.quiz.description, "Old Description")

    def test_patch_updates_description(self):
        response = self.client.patch(
            f"/api/quizzes/{self.quiz.id}/",
            {"description": "Updated Description"},
            format="json",
        )

        self.quiz.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.quiz.description,
            "Updated Description",
        )

    def test_patch_returns_400_for_invalid_data(self):
        response = self.client.patch(
            f"/api/quizzes/{self.quiz.id}/",
            {"title": ""},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_patch_returns_403_for_foreign_quiz(self):
        response = self.client.patch(
            f"/api/quizzes/{self.foreign_quiz.id}/",
            {"title": "Updated"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_patch_returns_404_for_unknown_quiz(self):
        response = self.client.patch(
            "/api/quizzes/999999/",
            {"title": "Updated"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_patch_requires_authentication(self):
        self.client.cookies.clear()

        response = self.client.patch(
            f"/api/quizzes/{self.quiz.id}/",
            {"title": "Updated"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )