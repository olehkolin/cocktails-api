from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class AuthTests(APITestCase):
    def test_register(self):
        data = {"username": "oleh", "email": "oleh@test.pl", "password": "Strong-pass-123"}
        response = self.client.post("/api/auth/register/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        user = User.objects.get(username="oleh")
        self.assertEqual(user.role, "user")
        # password should be hashed, not saved as plain text
        self.assertNotEqual(user.password, "Strong-pass-123")

    def test_register_with_weak_password(self):
        data = {"username": "oleh", "email": "oleh@test.pl", "password": "123"}
        response = self.client.post("/api/auth/register/", data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_with_taken_email(self):
        User.objects.create_user("anna", "same@test.pl", "Strong-pass-123")
        data = {"username": "oleh", "email": "same@test.pl", "password": "Strong-pass-123"}
        response = self.client.post("/api/auth/register/", data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_and_me(self):
        User.objects.create_user("oleh", "oleh@test.pl", "Strong-pass-123")

        response = self.client.post("/api/auth/login/", {"username": "oleh", "password": "Strong-pass-123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["access"])
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "oleh")

    def test_login_with_wrong_password(self):
        User.objects.create_user("oleh", "oleh@test.pl", "Strong-pass-123")
        response = self.client.post("/api/auth/login/", {"username": "oleh", "password": "wrong"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_without_token(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
