from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    """Raised when login credentials are invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid credentials."
    default_code = "invalid_credentials"


class InvalidRefreshToken(APIException):
    """Raised when the refresh token is missing or invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Refresh token is invalid or missing."
    default_code = "invalid_refresh_token"