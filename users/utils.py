from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from users.api.exceptions import InvalidRefreshToken


def create_auth_tokens(user):
    """Creates access and refresh tokens for a user."""
    refresh_token = RefreshToken.for_user(user)
    return (
        str(refresh_token.access_token),
        str(refresh_token),
    )


def create_access_token(refresh_token):
    """Creates an access token from a valid refresh token."""
    try:
        token = RefreshToken(refresh_token)
    except TokenError as error:
        raise InvalidRefreshToken() from error
    return str(token.access_token)


def get_refresh_token(request):
    """Returns the refresh token from the request cookie."""
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        raise InvalidRefreshToken()
    return refresh_token


def set_auth_cookies(response, access_token, refresh_token):
    """Sets both authentication cookies."""
    _set_auth_cookie(response, "access_token", access_token)
    _set_auth_cookie(response, "refresh_token", refresh_token)


def set_access_cookie(response, access_token):
    """Sets the access token cookie."""
    _set_auth_cookie(response, "access_token", access_token)


def _set_auth_cookie(response, name, token):
    """Sets a single HttpOnly authentication cookie."""
    response.set_cookie(
        key=name,
        value=token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def blacklist_auth_tokens(access_token, refresh_token, user):
    """Blacklists the current authentication tokens."""
    blacklist_access_token(access_token, user)
    if refresh_token:
        blacklist_refresh_token(refresh_token)


def blacklist_access_token(raw_token, user):
    """Adds an access token to the blacklist."""
    token = AccessToken(raw_token)
    outstanding_token = _get_outstanding_access_token(
        raw_token, token, user
    )
    BlacklistedToken.objects.get_or_create(token=outstanding_token)


def _get_outstanding_access_token(raw_token, token, user):
    """Returns or creates the database record for an access token."""
    token_record, _ = OutstandingToken.objects.get_or_create(
        jti=token["jti"],
        defaults=_get_token_defaults(raw_token, token, user),
    )
    return token_record


def _get_token_defaults(raw_token, token, user):
    """Builds database defaults for an outstanding access token."""
    return {
        "user": user,
        "token": raw_token,
        "created_at": _timestamp_to_datetime(token["iat"]),
        "expires_at": _timestamp_to_datetime(token["exp"]),
    }


def _timestamp_to_datetime(timestamp):
    """Converts a JWT timestamp to an aware datetime."""
    return datetime.fromtimestamp(
        timestamp,
        tz=dt_timezone.utc,
    )


def blacklist_refresh_token(raw_token):
    """Blacklists a refresh token if it is valid."""
    try:
        RefreshToken(raw_token).blacklist()
    except TokenError:
        return


def delete_auth_cookies(response):
    """Deletes access and refresh token cookies."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
