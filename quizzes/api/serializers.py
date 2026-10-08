from rest_framework import serializers

from quizzes.models import Question, Quiz
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
        """Allows only supported YouTube URLs."""
        hostname = urlparse(value).hostname or ""
        allowed_hosts = {
            "youtube.com",
            "www.youtube.com",
            "m.youtube.com",
            "youtu.be",
        }

        if hostname.lower() not in allowed_hosts:
            raise serializers.ValidationError(
                "Only YouTube URLs are supported."
            )

        return value