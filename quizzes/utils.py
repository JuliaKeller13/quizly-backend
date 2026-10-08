import shutil
import tempfile
from pathlib import Path

import whisper
from django.db import transaction
from google import genai
from rest_framework.exceptions import NotFound, PermissionDenied
from yt_dlp import YoutubeDL

from quizzes.models import Question, Quiz


QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "question_title": {"type": "string"},
        "question_options": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 4,
            "maxItems": 4,
        },
        "answer": {"type": "string"},
    },
    "required": [
        "question_title",
        "question_options",
        "answer",
    ],
}


QUIZ_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "questions": {
            "type": "array",
            "items": QUESTION_SCHEMA,
            "minItems": 10,
            "maxItems": 10,
        },
    },
    "required": [
        "title",
        "description",
        "questions",
    ],
}


def get_quiz_for_user(quiz_id, user):
    """Returns a quiz if it exists and belongs to the user."""
    try:
        quiz = Quiz.objects.prefetch_related("questions").get(id=quiz_id)
    except Quiz.DoesNotExist as error:
        raise NotFound("Quiz not found.") from error

    if quiz.user != user:
        raise PermissionDenied(
            "You do not have permission for this quiz."
        )

    return quiz


def create_quiz_from_video(video_url, user):
    """Runs the complete quiz generation pipeline."""
    audio_path = download_audio(video_url)

    try:
        transcript = transcribe_audio(audio_path)
        quiz_data = generate_quiz_data(transcript)
        return save_generated_quiz(quiz_data, video_url, user)
    finally:
        remove_audio_file(audio_path)


def download_audio(video_url):
    """Downloads YouTube audio and converts it to MP3."""
    temp_dir = tempfile.mkdtemp()
    output_template = str(
        Path(temp_dir) / "audio.%(ext)s"
    )
    options = get_download_options(output_template)

    with YoutubeDL(options) as downloader:
        downloader.download([video_url])

    return str(Path(temp_dir) / "audio.mp3")


def get_download_options(output_template):
    """Returns yt-dlp options for MP3 extraction."""
    return {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }
        ],
        "quiet": True,
    }


def transcribe_audio(audio_path):
    """Transcribes an audio file with Whisper."""
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result["text"].strip()


def generate_quiz_data(transcript):
    """Generates structured quiz data with Gemini."""
    client = genai.Client()

    try:
        response = request_quiz_data(client, transcript)
    finally:
        client.close()

    quiz_data = response.parsed
    validate_generated_quiz_data(quiz_data)
    return quiz_data


def request_quiz_data(client, transcript):
    """Requests structured quiz data from Gemini."""
    return client.models.generate_content(
        model="gemini-3.8-flash",
        contents=build_quiz_prompt(transcript),
        config=get_gemini_config(),
    )


def build_quiz_prompt(transcript):
    """Builds the prompt used to generate a quiz."""
    return (
        "Create an educational quiz using only the information "
        "in this transcript. Use the transcript's language. "
        "Each question must have exactly one correct answer.\n\n"
        f"Transcript:\n{transcript}"
    )


def get_gemini_config():
    """Returns Gemini structured-output configuration."""
    return {
        "response_mime_type": "application/json",
        "response_json_schema": QUIZ_RESPONSE_SCHEMA,
    }


def validate_generated_quiz_data(quiz_data):
    """Validates generated quiz structure."""
    required = {"title", "description", "questions"}

    if not required.issubset(quiz_data):
        raise ValueError("Generated quiz data is incomplete.")

    questions = quiz_data["questions"]

    if len(questions) != 10:
        raise ValueError("Generated quiz must contain 10 questions.")

    for question in questions:
        validate_generated_question(question)


def validate_generated_question(question):
    """Validates one generated quiz question."""
    required = {
        "question_title",
        "question_options",
        "answer",
    }

    if not required.issubset(question):
        raise ValueError("Generated question is incomplete.")

    options = question["question_options"]

    if len(options) != 4:
        raise ValueError("Each question must contain 4 options.")

    if question["answer"] not in options:
        raise ValueError("Answer must match one question option.")


def save_generated_quiz(quiz_data, video_url, user):
    """Saves generated quiz data and questions."""
    validate_generated_quiz_data(quiz_data)

    with transaction.atomic():
        quiz = create_quiz(quiz_data, video_url, user)
        questions = [
            build_question(quiz, data)
            for data in quiz_data["questions"]
        ]
        Question.objects.bulk_create(questions)

    return quiz


def create_quiz(quiz_data, video_url, user):
    """Creates the generated quiz database record."""
    return Quiz.objects.create(
        user=user,
        title=quiz_data["title"],
        description=quiz_data["description"],
        video_url=video_url,
    )


def build_question(quiz, question_data):
    """Builds an unsaved generated question."""
    return Question(
        quiz=quiz,
        question_title=question_data["question_title"],
        question_options=question_data["question_options"],
        answer=question_data["answer"],
    )


def remove_audio_file(audio_path):
    """Removes the temporary audio directory."""
    temp_dir = Path(audio_path).parent
    shutil.rmtree(
        temp_dir,
        ignore_errors=True,
    )