from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/", include("cocktails.urls")),
    # login button in the browsable API (easier for testing in browser)
    path("api-auth/", include("rest_framework.urls")),
]
