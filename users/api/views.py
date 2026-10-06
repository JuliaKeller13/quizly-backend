from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.utils import (
    create_access_token,
    create_auth_tokens,
    get_refresh_token,
    set_access_cookie,
    set_auth_cookies,
)

from .serializers import (
    LoginSerializer,
    RegistrationSerializer,
    UserSerializer,
)


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save()
        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        access_token, refresh_token = create_auth_tokens(user)
        user_data = UserSerializer(user).data
        response = self._create_response(user_data)
        set_auth_cookies(response, access_token, refresh_token)
        return response

    def _create_response(self, user_data):
        return Response(
            {
                "detail": "Login successfully!",
                "user": user_data,
            },
            status=status.HTTP_200_OK,
        )


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = get_refresh_token(request)
        access_token = create_access_token(refresh_token)

        response = Response(
            {"detail": "Token refreshed"},
            status=status.HTTP_200_OK,
        )
        set_access_cookie(response, access_token)
        return response