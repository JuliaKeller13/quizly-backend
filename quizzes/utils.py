import json
import shutil
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import whisper
from django.db import transaction
from google import genai
from rest_framework.exceptions import NotFound, PermissionDenied
from yt_dlp import YoutubeDL

from quizzes.models import Question, Quiz
from quizzes.prompts import QUIZ_PROMPT_TEMPLATE


YOUTUBE_PATH_PREFIXES = {"shorts", "embed"}


def get_quiz_for_user(quiz_id, user):
    """Returns a quiz if it exists and belongs to the user."""
    try:
        quiz = Quiz.objects.prefetch_related("questions").get(id=quiz_id)
    except Quiz.DoesNotExist as error:
        raise NotFound("Quiz not found.") from error
    _ensure_quiz_owner(quiz, user)
    return quiz


def _ensure_quiz_owner(quiz, user):
    """Rejects access to a quiz owned by another user."""
    if quiz.user != user:
        raise PermissionDenied("You do not have permission for this quiz.")


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
    output_template = str(Path(temp_dir) / "audio.%(ext)s")
    options = get_download_options(output_template)
    with YoutubeDL(options) as downloader:
        downloader.download([video_url])
    return str(Path(temp_dir) / "audio.mp3")


def _get_mp3_postprocessors():
    """Returns the FFmpeg configuration for MP3 extraction."""
    return [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }
    ]


def get_download_options(output_template):
    """Returns yt-dlp options for MP3 extraction."""
    return {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": _get_mp3_postprocessors(),
        "quiet": True,
        "noplaylist": True,
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
    quiz_data = parse_quiz_response(response.text)
    validate_generated_quiz_data(quiz_data)
    return quiz_data


def request_quiz_data(client, transcript):
    """Requests quiz data from Gemini."""
    return client.models.generate_content(
        model="gemini-3.5-flash",
        contents=build_quiz_prompt(transcript),
    )


def build_quiz_prompt(transcript):
    """Builds the prompt used to generate quiz data."""
    return f"{QUIZ_PROMPT_TEMPLATE}\nTranscript:\n{transcript}"


def validate_generated_quiz_data(quiz_data):
    """Validates generated quiz structure."""
    required = {"title", "description", "questions"}
    if not required.issubset(quiz_data):
        raise ValueError("Generated quiz data is incomplete.")
    questions = quiz_data["questions"]
    _validate_question_count(questions)
    for question in questions:
        validate_generated_question(question)


def _validate_question_count(questions):
    """Validates the required number of generated questions."""
    if len(questions) != 10:
        raise ValueError("Generated quiz must contain 10 questions.")


def validate_generated_question(question):
    """Validates one generated quiz question."""
    required = {"question_title", "question_options", "answer"}
    if not required.issubset(question):
        raise ValueError("Generated question is incomplete.")
    _validate_question_options(question)


def _validate_question_options(question):
    """Validates generated answer options."""
    options = question["question_options"]
    if len(options) != 4:
        raise ValueError("Each question must contain 4 options.")
    if len(set(options)) != 4:
        raise ValueError("Question options must be distinct.")
    if question["answer"] not in options:
        raise ValueError("Answer must match one question option.")


def save_generated_quiz(quiz_data, video_url, user):
    """Saves generated quiz data and questions."""
    validate_generated_quiz_data(quiz_data)
    with transaction.atomic():
        quiz = create_quiz(quiz_data, video_url, user)
        questions = build_questions(quiz, quiz_data["questions"])
        Question.objects.bulk_create(questions)
    return quiz


def build_questions(quiz, question_data):
    """Builds all unsaved questions for a generated quiz."""
    return [
        build_question(quiz, data)
        for data in question_data
    ]


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


def remove_markdown_fences(response_text):
    """Removes Markdown code fences from a Gemini response."""
    cleaned_text = response_text.strip()
    if cleaned_text.lower().startswith("```json"):
        cleaned_text = cleaned_text[7:]
    elif cleaned_text.startswith("```"):
        cleaned_text = cleaned_text[3:]
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3]
    return cleaned_text.strip()


def parse_quiz_response(response_text):
    """Parses Gemini response text into quiz data."""
    cleaned_text = remove_markdown_fences(response_text)
    return json.loads(cleaned_text)


def extract_youtube_video_id(url):
    """Extracts the video ID from a supported YouTube URL."""
    parsed_url = urlparse(url)
    if parsed_url.hostname == "youtu.be":
        return parsed_url.path.strip("/").split("/")[0]
    if parsed_url.path == "/watch":
        return parse_qs(parsed_url.query).get("v", [""])[0]
    return _extract_youtube_path_id(parsed_url.path)


def _extract_youtube_path_id(path):
    """Extracts a video ID from an embed or Shorts path."""
    path_parts = path.strip("/").split("/")
    if len(path_parts) == 2 and path_parts[0] in YOUTUBE_PATH_PREFIXES:
        return path_parts[1]
    return ""


def normalize_youtube_url(url):
    """Returns a YouTube URL in the canonical watch format."""
    video_id = extract_youtube_video_id(url)
    return f"https://www.youtube.com/watch?v={video_id}"
