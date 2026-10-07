from django.contrib.auth import get_user_model
from django.test import TestCase

from quizzes.models import Question, Quiz


User = get_user_model()


class QuizModelTests(TestCase):
    """Tests the quiz data model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="quizUser",
            email="quiz@example.com",
            password="ExamplePassword123!",
        )

    def test_quiz_belongs_to_user(self):
        """Ensures that a quiz belongs to its creator."""
        quiz = Quiz.objects.create(
            user=self.user,
            title="Quiz Title",
            description="Quiz Description",
            video_url="https://www.youtube.com/watch?v=example",
        )

        self.assertEqual(quiz.user, self.user)


class QuestionModelTests(TestCase):
    """Tests the question data model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="quizUser",
            email="quiz@example.com",
            password="ExamplePassword123!",
        )
        self.quiz = Quiz.objects.create(
            user=self.user,
            title="Quiz Title",
            description="Quiz Description",
            video_url="https://www.youtube.com/watch?v=example",
        )

    def test_question_belongs_to_quiz(self):
        """Ensures that a question belongs to its quiz."""
        question = Question.objects.create(
            quiz=self.quiz,
            question_title="Question 1",
            question_options=[
                "Option A",
                "Option B",
                "Option C",
                "Option D",
            ],
            answer="Option A",
        )

        self.assertEqual(question.quiz, self.quiz)