from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from quizzes.models import Question, Quiz


User = get_user_model()


class QuizDetailTests(APITestCase):
    """Tests the quiz detail endpoint."""

    def setUp(self):
        self.user = self._create_user("owner")
        self.other_user = self._create_user("other")
        self.quiz = self._create_quiz(self.user, "Own Quiz")
        self.foreign_quiz = self._create_quiz(
            self.other_user,
            "Foreign Quiz",
        )
        self._create_question()
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
            description="Description",
            video_url="https://www.youtube.com/watch?v=example",
        )

    def _create_question(self):
        Question.objects.create(
            quiz=self.quiz,
            question_title="Question 1",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )

    def _authenticate(self):
        refresh_token = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(
            refresh_token.access_token
        )

    def test_detail_returns_owned_quiz(self):
        response = self.client.get(
            f"/api/quizzes/{self.quiz.id}/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.quiz.id)
        self.assertEqual(response.data["title"], "Own Quiz")
        self.assertEqual(len(response.data["questions"]), 1)

    def test_detail_returns_403_for_foreign_quiz(self):
        response = self.client.get(
            f"/api/quizzes/{self.foreign_quiz.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_detail_returns_404_for_unknown_quiz(self):
        response = self.client.get("/api/quizzes/999999/")

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_detail_requires_authentication(self):
        self.client.cookies.clear()

        response = self.client.get(
            f"/api/quizzes/{self.quiz.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )