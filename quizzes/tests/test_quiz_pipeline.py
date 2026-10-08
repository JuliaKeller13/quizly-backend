import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from quizzes.models import Question, Quiz
from quizzes.utils import (
    build_quiz_prompt,
    create_quiz_from_video,
    download_audio,
    generate_quiz_data,
    get_download_options,
    request_quiz_data,
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
        self.video_url = "https://www.youtube.com/watch?v=example"

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
    def test_pipeline_creates_quiz(self, *mocks):
        """Runs all generation steps."""
        quiz = self._configure_pipeline(mocks)

        result = create_quiz_from_video(self.video_url, self.user)

        self._assert_pipeline_calls(mocks)
        self.assertEqual(result, quiz)

    def _configure_pipeline(self, mocks):
        """Configures successful pipeline mocks."""
        quiz = Quiz(user=self.user, title="Generated")
        mocks[0].return_value = "audio.mp3"
        mocks[1].return_value = "Transcript"
        mocks[2].return_value = self._quiz_data()
        mocks[3].return_value = quiz
        return quiz

    def _assert_pipeline_calls(self, mocks):
        """Checks calls made by the pipeline."""
        mocks[0].assert_called_once_with(self.video_url)
        mocks[1].assert_called_once_with("audio.mp3")
        mocks[2].assert_called_once_with("Transcript")
        expected = (self._quiz_data(), self.video_url, self.user)
        mocks[3].assert_called_once_with(*expected)
        mocks[4].assert_called_once_with("audio.mp3")

    @patch("quizzes.utils.remove_audio_file")
    @patch("quizzes.utils.transcribe_audio")
    @patch("quizzes.utils.download_audio")
    def test_pipeline_removes_audio_after_error(self, *mocks):
        """Removes temporary audio when processing fails."""
        mocks[0].return_value = "audio.mp3"
        mocks[1].side_effect = RuntimeError("Failure")

        with self.assertRaises(RuntimeError):
            create_quiz_from_video(self.video_url, self.user)

        mocks[2].assert_called_once_with("audio.mp3")

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
        mock_youtube_dl.return_value.__enter__.return_value = downloader

        result = download_audio(self.video_url)

        downloader.download.assert_called_once_with([self.video_url])
        self.assertEqual(result, str(Path("temp") / "audio.mp3"))

    def test_download_options_match_audio_requirements(self):
        """Returns the required yt-dlp audio options."""
        options = get_download_options("audio.%(ext)s")
        postprocessor = options["postprocessors"][0]

        self.assertEqual(options["format"], "bestaudio/best")
        self.assertEqual(options["outtmpl"], "audio.%(ext)s")
        self.assertTrue(options["quiet"])
        self.assertTrue(options["noplaylist"])
        self.assertEqual(postprocessor["key"], "FFmpegExtractAudio")
        self.assertEqual(postprocessor["preferredcodec"], "mp3")

    @patch("quizzes.utils.whisper.load_model")
    def test_transcribe_audio_uses_whisper(self, mock_load_model):
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
    def test_generate_quiz_data_uses_gemini(self, mock_client):
        """Generates structured quiz data with Gemini."""
        client = MagicMock()
        response = MagicMock()
        response.text = json.dumps(self._quiz_data())
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

    def test_generated_question_requires_distinct_options(self):
        """Rejects duplicate answer options."""
        quiz_data = self._quiz_data()
        quiz_data["questions"][0]["question_options"] = [
            "A",
            "A",
            "C",
            "D",
        ]

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
    def test_remove_audio_file_removes_temp_directory(self, mock_rmtree):
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

    def test_build_quiz_prompt_contains_required_instructions(self):
        """Builds a prompt with the required quiz structure."""
        prompt = build_quiz_prompt("Transcript text")

        self.assertIn("valid JSON format", prompt)
        self.assertIn("exactly 10 questions", prompt)
        self.assertIn("exactly 4 distinct answer options", prompt)
        self.assertIn("no more than 150 characters", prompt)
        self.assertIn("Do not include any quiz questions or answers", prompt)
        self.assertIn("Transcript text", prompt)

    @patch("quizzes.utils.build_quiz_prompt", return_value="PROMPT")
    def test_request_quiz_data_uses_plain_text_response(
        self,
        mock_build_prompt,
    ):
        """Requests quiz data without structured output config."""
        client = MagicMock()

        request_quiz_data(client, "Transcript")

        mock_build_prompt.assert_called_once_with("Transcript")
        client.models.generate_content.assert_called_once_with(
            model="gemini-3.5-flash",
            contents="PROMPT",
        )
