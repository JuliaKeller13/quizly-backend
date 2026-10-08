import json

from django.test import SimpleTestCase

from quizzes.utils import parse_quiz_response, remove_markdown_fences


class GeminiResponseTests(SimpleTestCase):
    """Tests processing of Gemini quiz responses."""

    def setUp(self):
        """Creates valid quiz data for the tests."""
        self.quiz_data = {
            "title": "HTML Quiz",
            "description": "A short quiz about HTML.",
            "questions": [
                {
                    "question_title": f"Question {number}",
                    "question_options": ["A", "B", "C", "D"],
                    "answer": "A",
                }
                for number in range(10)
            ],
        }

    def test_removes_json_markdown_fences(self):
        """Removes JSON Markdown code fences."""
        response_text = f"```json\n{json.dumps(self.quiz_data)}\n```"

        cleaned_text = remove_markdown_fences(response_text)

        self.assertEqual(json.loads(cleaned_text), self.quiz_data)

    def test_removes_plain_markdown_fences(self):
        """Removes plain Markdown code fences."""
        response_text = f"```\n{json.dumps(self.quiz_data)}\n```"

        cleaned_text = remove_markdown_fences(response_text)

        self.assertEqual(json.loads(cleaned_text), self.quiz_data)

    def test_parses_plain_json_response(self):
        """Parses a valid plain JSON Gemini response."""
        response_text = json.dumps(self.quiz_data)

        result = parse_quiz_response(response_text)

        self.assertEqual(result, self.quiz_data)

    def test_parses_markdown_json_response(self):
        """Parses a JSON response wrapped in Markdown."""
        response_text = f"```json\n{json.dumps(self.quiz_data)}\n```"

        result = parse_quiz_response(response_text)

        self.assertEqual(result, self.quiz_data)