from django.contrib.auth import get_user_model
from django.test import TestCase

from quizzes.models import Question, Quiz


User = get_user_model()


class QuizModelTests(TestCase):
    """Tests the quiz data model."""

    def setUp(self):
        """Creates common quiz test data."""
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

    def test_quiz_belongs_to_user(self):
        """Ensures that a quiz belongs to its creator."""
        self.assertEqual(self.quiz.user, self.user)

    def test_quiz_string_returns_title(self):
        """Returns the quiz title as string representation."""
        self.assertEqual(str(self.quiz), self.quiz.title)


class QuestionModelTests(TestCase):
    """Tests the question data model."""

    def setUp(self):
        """Creates common question test data."""
        self.user = User.objects.create_user(
            username="quizUser",
            email="quiz@example.com",
            password="ExamplePassword123!",
        )
        self.quiz = self._create_quiz()
        self.question = self._create_question()

    def _create_quiz(self):
        """Creates a quiz for question tests."""
        return Quiz.objects.create(
            user=self.user,
            title="Quiz Title",
            description="Quiz Description",
            video_url="https://www.youtube.com/watch?v=example",
        )

    def _create_question(self):
        """Creates a question for the test quiz."""
        return Question.objects.create(
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

    def test_question_belongs_to_quiz(self):
        """Ensures that a question belongs to its quiz."""
        self.assertEqual(self.question.quiz, self.quiz)

    def test_deleting_quiz_deletes_questions(self):
        """Ensures that deleting a quiz removes its questions."""
        question_id = self.question.id

        self.quiz.delete()

        self.assertFalse(
            Question.objects.filter(id=question_id).exists()
        )

    def test_question_options_are_stored_as_list(self):
        """Ensures that question options are stored as a list."""
        expected_options = [
            "Option A",
            "Option B",
            "Option C",
            "Option D",
        ]

        self.assertEqual(
            self.question.question_options,
            expected_options,
        )

    def test_question_string_returns_title(self):
        """Returns the question title as string representation."""
        self.assertEqual(
            str(self.question),
            self.question.question_title,
        )