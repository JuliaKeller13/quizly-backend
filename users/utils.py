from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from users.api.exceptions import InvalidRefreshToken


def create_auth_tokens(user):
    refresh_token = RefreshToken.for_user(user)

    return (
        str(refresh_token.access_token),
        str(refresh_token),
    )


def create_access_token(refresh_token):
    try:
        token = RefreshToken(refresh_token)
    except TokenError as error:
        raise InvalidRefreshToken() from error

    return str(token.access_token)


def get_refresh_token(request):
    refresh_token = request.COOKIES.get("refresh_token")

    if not refresh_token:
        raise InvalidRefreshToken()

    return refresh_token


def set_auth_cookies(response, access_token, refresh_token):
    _set_auth_cookie(response, "access_token", access_token)
    _set_auth_cookie(response, "refresh_token", refresh_token)


def set_access_cookie(response, access_token):
    _set_auth_cookie(response, "access_token", access_token)


def _set_auth_cookie(response, name, token):
    response.set_cookie(
        key=name,
        value=token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )