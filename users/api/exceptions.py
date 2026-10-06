from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidCredentials(APIException):
    """Raised when login credentials are invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid credentials."
    default_code = "invalid_credentials"