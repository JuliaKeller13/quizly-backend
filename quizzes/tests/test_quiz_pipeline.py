from pathlib import Path
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from quizzes.models import Question, Quiz
from quizzes.utils import (
    create_quiz_from_video,
    download_audio,
    generate_quiz_data,
    remove_audio_file,
    save_generated_quiz,
    transcribe_audio,
    validate_generated_quiz_data,
)


User = get_user_model()


class QuizPipelineTests(TestCase):
    """Tests the complete quiz generation pipeline."""

    def setUp(self):
        """Creates common test data."""
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="ExamplePassword123!",
        )
        self.video_url = (
            "https://www.youtube.com/watch?v=example"
        )

    def _question_data(self, number):
        """Returns generated data for one question."""
        return {
            "question_title": f"Question {number}",
            "question_options": ["A", "B", "C", "D"],
            "answer": "A",
        }

    def _quiz_data(self):
        """Returns valid generated quiz data."""
        return {
            "title": "Generated Quiz",
            "description": "Generated Description",
            "questions": [
                self._question_data(number)
                for number in range(1, 11)
            ],
        }

    @patch("quizzes.utils.remove_audio_file")
    @patch("quizzes.utils.save_generated_quiz")
    @patch("quizzes.utils.generate_quiz_data")
    @patch("quizzes.utils.transcribe_audio")
    @patch("quizzes.utils.download_audio")
    def test_pipeline_creates_quiz(
        self,
        mock_download,
        mock_transcribe,
        mock_generate,
        mock_save,
        mock_remove,
    ):
        """Runs all generation steps."""
        quiz = self._configure_pipeline(
            mock_download,
            mock_transcribe,
            mock_generate,
            mock_save,
        )
        result = create_quiz_from_video(
            self.video_url,
            self.user,
        )
        self._assert_pipeline_calls(
            mock_download,
            mock_transcribe,
            mock_generate,
            mock_save,
            mock_remove,
        )
        self.assertEqual(result, quiz)

    def _configure_pipeline(
        self,
        mock_download,
        mock_transcribe,
        mock_generate,
        mock_save,
    ):
        """Configures successful pipeline mocks."""
        quiz = Quiz(user=self.user, title="Generated")
        mock_download.return_value = "audio.mp3"
        mock_transcribe.return_value = "Transcript"
        mock_generate.return_value = self._quiz_data()
        mock_save.return_value = quiz
        return quiz

    def _assert_pipeline_calls(
        self,
        mock_download,
        mock_transcribe,
        mock_generate,
        mock_save,
        mock_remove,
    ):
        """Checks calls made by the pipeline."""
        mock_download.assert_called_once_with(self.video_url)
        mock_transcribe.assert_called_once_with("audio.mp3")
        mock_generate.assert_called_once_with("Transcript")
        mock_save.assert_called_once_with(
            self._quiz_data(),
            self.video_url,
            self.user,
        )
        mock_remove.assert_called_once_with("audio.mp3")

    @patch("quizzes.utils.remove_audio_file")
    @patch("quizzes.utils.transcribe_audio")
    @patch("quizzes.utils.download_audio")
    def test_pipeline_removes_audio_after_error(
        self,
        mock_download,
        mock_transcribe,
        mock_remove,
    ):
        """Removes temporary audio when processing fails."""
        mock_download.return_value = "audio.mp3"
        mock_transcribe.side_effect = RuntimeError("Failure")

        with self.assertRaises(RuntimeError):
            create_quiz_from_video(self.video_url, self.user)

        mock_remove.assert_called_once_with("audio.mp3")

    @patch("quizzes.utils.YoutubeDL")
    @patch("quizzes.utils.tempfile.mkdtemp")
    def test_download_audio_uses_youtube_dl(
        self,
        mock_mkdtemp,
        mock_youtube_dl,
    ):
        """Downloads audio into a temporary directory."""
        mock_mkdtemp.return_value = "temp"
        downloader = MagicMock()
        mock_youtube_dl.return_value.__enter__.return_value = (
            downloader
        )

        result = download_audio(self.video_url)

        downloader.download.assert_called_once_with([self.video_url])
        self.assertEqual(
            result,
            str(Path("temp") / "audio.mp3"),
        )

    @patch("quizzes.utils.whisper.load_model")
    def test_transcribe_audio_uses_whisper(
        self,
        mock_load_model,
    ):
        """Transcribes downloaded audio with Whisper."""
        model = MagicMock()
        mock_load_model.return_value = model
        model.transcribe.return_value = {
            "text": " Generated transcript ",
        }

        result = transcribe_audio("audio.mp3")

        mock_load_model.assert_called_once_with("base")
        model.transcribe.assert_called_once_with("audio.mp3")
        self.assertEqual(result, "Generated transcript")

    @patch("quizzes.utils.genai.Client")
    def test_generate_quiz_data_uses_gemini(
        self,
        mock_client,
    ):
        """Generates structured quiz data with Gemini."""
        client = MagicMock()
        response = MagicMock()
        response.parsed = self._quiz_data()
        mock_client.return_value = client
        client.models.generate_content.return_value = response

        result = generate_quiz_data("Transcript")

        client.models.generate_content.assert_called_once()
        self.assertEqual(result, self._quiz_data())

    def test_generated_data_requires_ten_questions(self):
        """Rejects generated data without ten questions."""
        quiz_data = self._quiz_data()
        quiz_data["questions"].pop()

        with self.assertRaises(ValueError):
            validate_generated_quiz_data(quiz_data)

    def test_generated_question_requires_four_options(self):
        """Rejects questions without four answer options."""
        quiz_data = self._quiz_data()
        quiz_data["questions"][0]["question_options"].pop()

        with self.assertRaises(ValueError):
            validate_generated_quiz_data(quiz_data)

    def test_save_generated_quiz_creates_quiz(self):
        """Saves generated quiz information."""
        quiz = save_generated_quiz(
            self._quiz_data(),
            self.video_url,
            self.user,
        )

        self.assertEqual(Quiz.objects.count(), 1)
        self.assertEqual(quiz.user, self.user)
        self.assertEqual(quiz.title, "Generated Quiz")
        self.assertEqual(quiz.video_url, self.video_url)

    def test_save_generated_quiz_creates_questions(self):
        """Saves all ten generated questions."""
        quiz = save_generated_quiz(
            self._quiz_data(),
            self.video_url,
            self.user,
        )

        self.assertEqual(Question.objects.count(), 10)
        self.assertEqual(quiz.questions.count(), 10)
        self.assertEqual(
            quiz.questions.first().question_options,
            ["A", "B", "C", "D"],
        )

    @patch("quizzes.utils.shutil.rmtree")
    def test_remove_audio_file_removes_temp_directory(
        self,
        mock_rmtree,
    ):
        """Removes the directory containing temporary audio."""
        audio_path = str(Path("temp") / "audio.mp3")

        remove_audio_file(audio_path)

        mock_rmtree.assert_called_once_with(
            Path(audio_path).parent,
            ignore_errors=True,
        )

    def test_generated_data_requires_all_fields(self):
        """Rejects generated quiz data with missing fields."""
        quiz_data = self._quiz_data()
        quiz_data.pop("title")

        with self.assertRaises(ValueError):
            validate_generated_quiz_data(quiz_data)


    def test_generated_question_requires_all_fields(self):
        """Rejects generated questions with missing fields."""
        quiz_data = self._quiz_data()
        quiz_data["questions"][0].pop("answer")

        with self.assertRaises(ValueError):
            validate_generated_quiz_data(quiz_data)


    def test_generated_answer_must_match_option(self):
        """Rejects answers not contained in question options."""
        quiz_data = self._quiz_data()
        quiz_data["questions"][0]["answer"] = "Wrong answer"

        with self.assertRaises(ValueError):
            validate_generated_quiz_data(quiz_data)