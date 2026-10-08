from rest_framework import serializers

from quizzes.models import Question, Quiz
from quizzes.utils import (
    extract_youtube_video_id,
    normalize_youtube_url,
)
from urllib.parse import urlparse


class QuestionSerializer(serializers.ModelSerializer):
    """Serializes quiz questions."""

    class Meta:
        model = Question
        fields = [
            "id",
            "question_title",
            "question_options",
            "answer",
        ]


class QuizSerializer(serializers.ModelSerializer):
    """Serializes quizzes including their questions."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]


class QuizUpdateSerializer(serializers.ModelSerializer):
    """Validates editable quiz fields."""

    class Meta:
        model = Quiz
        fields = [
            "title",
            "description",
        ]


class QuizCreateSerializer(serializers.Serializer):
    """Validates quiz creation requests."""

    url = serializers.URLField()

    def validate_url(self, value):
        """Validates and normalizes a YouTube video URL."""
        parsed_url = urlparse(value)
        allowed_hosts = {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
        }

        if parsed_url.hostname not in allowed_hosts:
            raise serializers.ValidationError("Only YouTube URLs are allowed.")

        if not extract_youtube_video_id(value):
            raise serializers.ValidationError("Invalid YouTube video URL.")

        return normalize_youtube_url(value)