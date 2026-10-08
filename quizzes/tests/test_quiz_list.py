from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from quizzes.models import Question, Quiz


User = get_user_model()


class QuizListTests(APITestCase):
    """Tests the quiz list endpoint."""

    def setUp(self):
        self.url = "/api/quizzes/"
        self.user = self._create_user("owner")
        self.other_user = self._create_user("other")
        self.quiz = self._create_quiz(self.user, "Own Quiz")
        self._create_quiz(self.other_user, "Foreign Quiz")
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
        access_token = str(refresh_token.access_token)
        self.client.cookies["access_token"] = access_token

    def test_list_returns_only_owned_quizzes(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.quiz.id)
        self.assertEqual(response.data[0]["title"], "Own Quiz")

    def test_list_contains_questions(self):
        response = self.client.get(self.url)

        questions = response.data[0]["questions"]

        self.assertEqual(len(questions), 1)
        self.assertEqual(
            questions[0]["question_title"],
            "Question 1",
        )

    def test_list_requires_authentication(self):
        self.client.cookies.clear()

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )