from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quizzes.utils import get_quiz_for_user
from quizzes.models import Quiz

from .serializers import QuizSerializer, QuizUpdateSerializer


class QuizListView(APIView):
    """Lists quizzes belonging to the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Returns only quizzes owned by the current user."""
        quizzes = Quiz.objects.filter(
            user=request.user
        ).prefetch_related("questions")
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data)


class QuizDetailView(APIView):
    """Handles operations for a single owned quiz."""

    permission_classes = [IsAuthenticated]

    def get(self, request, quiz_id):
        """Returns one quiz including its questions."""
        quiz = get_quiz_for_user(quiz_id, request.user)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)

    def patch(self, request, quiz_id):
        """Partially updates an owned quiz."""
        quiz = get_quiz_for_user(quiz_id, request.user)
        serializer = QuizUpdateSerializer(
            quiz,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(QuizSerializer(quiz).data)

    def delete(self, request, quiz_id):
        """Deletes an owned quiz."""
        quiz = get_quiz_for_user(quiz_id, request.user)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)