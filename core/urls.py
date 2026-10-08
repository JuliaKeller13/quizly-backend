from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/", include("users.api.urls")),
    path("api/", include("quizzes.api.urls")),
]
