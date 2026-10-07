from django.contrib import admin

from .models import Question, Quiz


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Configures quizzes in the Django admin."""

    list_display = (
        "id",
        "title",
        "user",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "title",
        "user__username",
    )


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Configures questions in the Django admin."""

    list_display = (
        "id",
        "question_title",
        "quiz",
        "created_at",
    )
    search_fields = (
        "question_title",
        "quiz__title",
    )