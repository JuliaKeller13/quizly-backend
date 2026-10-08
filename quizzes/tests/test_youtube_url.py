from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from quizzes.api.serializers import QuizCreateSerializer
from quizzes.models import Quiz
from quizzes.utils import normalize_youtube_url


class YoutubeUrlTests(SimpleTestCase):
    """Tests normalization of supported YouTube URLs."""

    def test_normalizes_standard_youtube_url(self):
        """Keeps the video ID and removes additional parameters."""
        url = "https://www.youtube.com/watch?v=abc123XYZ89&t=120"

        result = normalize_youtube_url(url)

        self.assertEqual(
            result,
            "https://www.youtube.com/watch?v=abc123XYZ89",
        )

    def test_normalizes_short_youtube_url(self):
        """Converts a youtu.be URL to the canonical format."""
        url = "https://youtu.be/abc123XYZ89"

        result = normalize_youtube_url(url)

        self.assertEqual(
            result,
            "https://www.youtube.com/watch?v=abc123XYZ89",
        )

    def test_normalizes_shorts_url(self):
        """Converts a YouTube Shorts URL to the canonical format."""
        url = "https://www.youtube.com/shorts/abc123XYZ89"

        result = normalize_youtube_url(url)

        self.assertEqual(
            result,
            "https://www.youtube.com/watch?v=abc123XYZ89",
        )

    def test_normalizes_embed_url(self):
        """Converts a YouTube embed URL to the canonical format."""
        url = "https://www.youtube.com/embed/abc123XYZ89"

        result = normalize_youtube_url(url)

        self.assertEqual(
            result,
            "https://www.youtube.com/watch?v=abc123XYZ89",
        )

    def test_quiz_serializer_normalizes_youtube_url(self):
        """Returns the canonical YouTube URL after validation."""
        serializer = QuizCreateSerializer(
            data={"url": "https://youtu.be/abc123XYZ89"},
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data["url"],
            "https://www.youtube.com/watch?v=abc123XYZ89",
        )

    def test_rejects_youtube_url_without_video_id(self):
        """Rejects a YouTube watch URL without a video ID."""
        serializer = QuizCreateSerializer(
            data={"url": "https://www.youtube.com/watch"},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("url", serializer.errors)

    def test_rejects_unsupported_youtube_path(self):
        """Rejects YouTube URLs that do not point to a video."""
        serializer = QuizCreateSerializer(
            data={"url": "https://www.youtube.com/channel/abc123XYZ89"},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("url", serializer.errors)


class YoutubeUrlDatabaseTests(TestCase):
    """Tests persistence of normalized YouTube URLs."""

    def setUp(self):
        """Creates an authenticated API client."""
        self.user = get_user_model().objects.create_user(
            username="urluser",
            password="TestPassword123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _quiz_data(self):
        """Returns valid generated quiz data."""
        return {
            "title": "HTML Quiz",
            "description": "A quiz about HTML.",
            "questions": [
                self._question_data(number)
                for number in range(10)
            ],
        }

    def _question_data(self, number):
        """Returns one valid generated question."""
        return {
            "question_title": f"Question {number}",
            "question_options": ["A", "B", "C", "D"],
            "answer": "A",
        }

    def _configure_pipeline_mocks(self, mocks):
        """Configures mocked quiz-generation steps."""
        mocks[0].return_value = "audio.mp3"
        mocks[1].return_value = "Transcript"
        mocks[2].return_value = self._quiz_data()

    @patch("quizzes.utils.remove_audio_file")
    @patch("quizzes.utils.generate_quiz_data")
    @patch("quizzes.utils.transcribe_audio")
    @patch("quizzes.utils.download_audio")
    def test_saves_canonical_youtube_url(self, *mocks):
        """Saves the canonical YouTube watch URL."""
        self._configure_pipeline_mocks(mocks)

        response = self.client.post(
            "/api/quizzes/",
            {"url": "https://youtu.be/abc123XYZ89"},
            format="json",
        )
        quiz = Quiz.objects.get(user=self.user)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(quiz.video_url, self._canonical_url())
        mocks[3].assert_called_once_with("audio.mp3")

    def _canonical_url(self):
        """Returns the expected canonical video URL."""
        return "https://www.youtube.com/watch?v=abc123XYZ89"
