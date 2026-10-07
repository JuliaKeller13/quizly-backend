from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Represents an authenticated Quizly user."""

    email = models.EmailField(unique=True)