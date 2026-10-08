from rest_framework.exceptions import NotFound, PermissionDenied

from quizzes.models import Quiz


def get_quiz_for_user(quiz_id, user):
    """Returns a quiz if it exists and belongs to the user."""
    try:
        quiz = Quiz.objects.prefetch_related("questions").get(id=quiz_id)
    except Quiz.DoesNotExist as error:
        raise NotFound("Quiz not found.") from error

    if quiz.user != user:
        raise PermissionDenied("You do not have permission for this quiz.")

    return quiz