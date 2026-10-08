from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from quizzes.models import Question, Quiz


User = get_user_model()


class QuizDeleteTests(APITestCase):
    """Tests the quiz delete endpoint."""

    def setUp(self):
        self.user = self._create_user("owner")
        self.other_user = self._create_user("other")
        self.quiz = self._create_quiz(self.user, "Own Quiz")
        self.foreign_quiz = self._create_quiz(
            self.other_user,
            "Foreign Quiz",
        )
        self.question = self._create_question()
        self._authenticate()

    def _create_user(self, username):
        """Creates a test user."""
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="ExamplePassword123!",
        )

    def _create_quiz(self, user, title):
        """Creates a quiz for a test user."""
        return Quiz.objects.create(
            user=user,
            title=title,
            description="Description",
            video_url="https://www.youtube.com/watch?v=example",
        )

    def _create_question(self):
        """Creates a question for the owned quiz."""
        return Question.objects.create(
            quiz=self.quiz,
            question_title="Question 1",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )

    def _authenticate(self):
        """Sets an access-token cookie."""
        refresh_token = RefreshToken.for_user(self.user)
        self.client.cookies["access_token"] = str(
            refresh_token.access_token
        )

    def test_delete_removes_owned_quiz(self):
        """Deletes a quiz owned by the user."""
        response = self.client.delete(
            f"/api/quizzes/{self.quiz.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            Quiz.objects.filter(id=self.quiz.id).exists()
        )

    def test_delete_removes_related_questions(self):
        """Deletes questions belonging to the deleted quiz."""
        self.client.delete(
            f"/api/quizzes/{self.quiz.id}/"
        )

        self.assertFalse(
            Question.objects.filter(id=self.question.id).exists()
        )

    def test_delete_returns_403_for_foreign_quiz(self):
        """Rejects deletion of another user's quiz."""
        response = self.client.delete(
            f"/api/quizzes/{self.foreign_quiz.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_returns_404_for_unknown_quiz(self):
        """Returns 404 when the quiz does not exist."""
        response = self.client.delete(
            "/api/quizzes/999999/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_delete_requires_authentication(self):
        """Rejects unauthenticated deletion requests."""
        self.client.cookies.clear()

        response = self.client.delete(
            f"/api/quizzes/{self.quiz.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )