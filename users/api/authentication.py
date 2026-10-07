from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticates users with the access token cookie."""

    def authenticate(self, request):
        """Authenticates a request using its access-token cookie."""
        raw_token = request.COOKIES.get("access_token")

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        self._check_blacklist(validated_token)
        user = self.get_user(validated_token)
        return user, validated_token

    def _check_blacklist(self, token):
        """Rejects access tokens stored in the blacklist."""
        is_blacklisted = BlacklistedToken.objects.filter(
            token__jti=token["jti"]
        ).exists()

        if is_blacklisted:
            raise InvalidToken("Token is blacklisted.")