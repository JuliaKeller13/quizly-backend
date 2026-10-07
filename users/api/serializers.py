import re

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from users.models import User

from .exceptions import InvalidCredentials


PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}$"
)


class UserSerializer(serializers.ModelSerializer):
    """Serializes public user data."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
        ]


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates registration data and creates users."""

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "confirmed_password",
            "email",
        ]
        extra_kwargs = {
            "username": {"min_length": 3},
            "password": {"write_only": True},
            "email": {
                "required": True,
                "allow_blank": False,
                "validators": [],
            },
        }

    def validate_email(self, value):
        """Rejects email addresses that are already registered."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate_password(self, value):
        """Validates password strength."""
        if not PASSWORD_PATTERN.match(value):
            raise serializers.ValidationError(
                "Password does not meet the requirements."
            )
        validate_password(value)
        return value

    def validate(self, attrs):
        """Checks whether both password fields match."""
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Creates a user with a hashed password."""
        validated_data.pop("confirmed_password")
        password = validated_data.pop("password")

        return User.objects.create_user(
            password=password,
            **validated_data,
        )


class LoginSerializer(serializers.Serializer):
    """Validates user login credentials."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticates the supplied username and password."""
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )

        if user is None:
            raise InvalidCredentials()

        attrs["user"] = user
        return attrs