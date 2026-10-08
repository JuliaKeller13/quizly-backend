from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from quizzes.models import Question, Quiz


User = get_user_model()


class QuizCreateTests(APITestCase):
    """Tests the quiz creation endpoint."""

    def setUp(self):
        self.url = "/api/quizzes/"
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="ExamplePassword123!",
        )
        self._authenticate()

    def _authenticate(self):
        """Sets an access-token cookie."""
        refresh_token = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(
            refresh_token.access_token
        )

    def _create_generated_quiz(self):
        """Creates a quiz representing generated pipeline output."""
        quiz = Quiz.objects.create(
            user=self.user,
            title="Generated Quiz",
            description="Generated Description",
            video_url="https://www.youtube.com/watch?v=example",
        )
        self._create_questions(quiz)
        return quiz

    def _create_questions(self, quiz):
        """Creates ten generated questions."""
        for number in range(10):
            Question.objects.create(
                quiz=quiz,
                question_title=f"Question {number + 1}",
                question_options=["A", "B", "C", "D"],
                answer="A",
            )

    @patch("quizzes.api.views.create_quiz_from_video")
    def test_post_creates_quiz(self, mock_create_quiz):
        """Returns generated quiz with ten questions."""
        mock_create_quiz.return_value = self._create_generated_quiz()

        response = self.client.post(
            self.url,
            {"url": "https://www.youtube.com/watch?v=example"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Generated Quiz")
        self.assertEqual(len(response.data["questions"]), 10)

    def test_post_rejects_missing_url(self):
        """Rejects requests without a video URL."""
        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_post_requires_authentication(self):
        """Rejects unauthenticated quiz creation."""
        self.client.cookies.clear()

        response = self.client.post(
            self.url,
            {"url": "https://www.youtube.com/watch?v=example"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_post_rejects_non_youtube_url(self):
        """Rejects URLs that do not point to YouTube."""
        response = self.client.post(
            self.url,
            {"url": "https://example.com/video"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )