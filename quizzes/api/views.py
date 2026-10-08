from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quizzes.models import Quiz

from .serializers import QuizSerializer


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