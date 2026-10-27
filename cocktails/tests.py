from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User

from .models import Cocktail, CocktailIngredient, Ingredient, Review


class BaseTestCase(APITestCase):
    """Creates some users, ingredients and one cocktail for all tests."""

    # setUpTestData runs once for the whole class (faster than setUp)
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("oleh", "oleh@test.pl", "Strong-pass-123")
        cls.other_user = User.objects.create_user("anna", "anna@test.pl", "Strong-pass-123")
        cls.admin = User.objects.create_user("boss", "boss@test.pl", "Strong-pass-123", role="admin")

        cls.rum = Ingredient.objects.create(name="Rum", is_alcoholic=True)
        cls.vodka = Ingredient.objects.create(name="Vodka", is_alcoholic=True)
        cls.mint = Ingredient.objects.create(name="Mint")
        cls.lime = Ingredient.objects.create(name="Lime juice")

        cls.mojito = Cocktail.objects.create(
            name="Mojito", category="highball", instructions="Mix it.", author=cls.user
        )
        CocktailIngredient.objects.create(cocktail=cls.mojito, ingredient=cls.rum, amount=50, unit="ml")
        CocktailIngredient.objects.create(cocktail=cls.mojito, ingredient=cls.mint, amount=8, unit="leaf")

    def cocktail_data(self, **changes):
        data = {
            "name": "Virgin Mojito",
            "category": "highball",
            "instructions": "Mix mint with lime.",
            "ingredients": [
                {"ingredient_id": self.mint.id, "amount": 8, "unit": "leaf"},
                {"ingredient_id": self.lime.id, "amount": 25, "unit": "ml"},
            ],
        }
        data.update(changes)
        return data


class IngredientTests(BaseTestCase):
    def test_list_is_public_and_paginated(self):
        response = self.client.get("/api/ingredients/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 4)
        self.assertIn("results", response.data)

    def test_create_needs_login(self):
        response = self.client.post("/api/ingredients/", {"name": "Basil"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create(self):
        self.client.force_authenticate(self.user)
        data = {"name": "Basil", "description": "Herb", "image_url": "https://example.com/basil.jpg"}
        response = self.client.post("/api/ingredients/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Ingredient.objects.filter(name="Basil").exists())

    def test_name_must_be_unique_ignoring_case(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/ingredients/", {"name": "MINT"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_image_url(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/ingredients/", {"name": "Basil", "image_url": "not-a-url"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_normal_user_cant_edit(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(f"/api/ingredients/{self.lime.id}/", {"description": "new"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_edit(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(f"/api/ingredients/{self.lime.id}/", {"description": "new"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lime.refresh_from_db()
        self.assertEqual(self.lime.description, "new")

    def test_cant_delete_ingredient_used_in_cocktail(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f"/api/ingredients/{self.mint.id}/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Ingredient.objects.filter(id=self.mint.id).exists())

    def test_admin_can_delete_unused_ingredient(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f"/api/ingredients/{self.vodka.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_filter_by_alcoholic(self):
        response = self.client.get("/api/ingredients/?is_alcoholic=true")
        names = [i["name"] for i in response.data["results"]]
        self.assertEqual(names, ["Rum", "Vodka"])

    def test_wrong_filter_value(self):
        response = self.client.get("/api/ingredients/?is_alcoholic=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CocktailTests(BaseTestCase):
    def test_list_is_public(self):
        response = self.client.get("/api/cocktails/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        mojito = response.data["results"][0]
        self.assertEqual(mojito["author"], "oleh")
        self.assertTrue(mojito["is_alcoholic"])
        self.assertEqual(len(mojito["ingredients"]), 2)

    def test_create_needs_login(self):
        response = self.client.post("/api/cocktails/", self.cocktail_data(), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create(self):
        self.client.force_authenticate(self.other_user)
        response = self.client.post("/api/cocktails/", self.cocktail_data(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], "anna")
        self.assertFalse(response.data["is_alcoholic"])
        cocktail = Cocktail.objects.get(name="Virgin Mojito")
        self.assertEqual(cocktail.cocktail_ingredients.count(), 2)

    def test_create_without_ingredients(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/cocktails/", self.cocktail_data(ingredients=[]), format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ingredients", response.data)

    def test_create_with_same_ingredient_twice(self):
        self.client.force_authenticate(self.user)
        ingredients = [
            {"ingredient_id": self.mint.id, "amount": 8, "unit": "leaf"},
            {"ingredient_id": self.mint.id, "amount": 2, "unit": "leaf"},
        ]
        response = self.client.post("/api/cocktails/", self.cocktail_data(ingredients=ingredients), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_wrong_data(self):
        self.client.force_authenticate(self.user)
        ingredients = [
            {"ingredient_id": self.mint.id, "amount": -5, "unit": "leaf"},
            {"ingredient_id": 9999, "amount": 10, "unit": "ml"},
        ]
        data = self.cocktail_data(name="", category="wrong", ingredients=ingredients)
        response = self.client.post("/api/cocktails/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("category", response.data)
        self.assertIn("ingredients", response.data)
        self.assertEqual(Cocktail.objects.count(), 1)

    def test_author_can_update(self):
        self.client.force_authenticate(self.user)
        data = self.cocktail_data(name="Mojito 2")
        response = self.client.put(f"/api/cocktails/{self.mojito.id}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mojito.refresh_from_db()
        self.assertEqual(self.mojito.name, "Mojito 2")
        # old ingredients should be replaced with new ones
        ingredient_ids = set(self.mojito.cocktail_ingredients.values_list("ingredient_id", flat=True))
        self.assertEqual(ingredient_ids, {self.mint.id, self.lime.id})

    def test_patch_without_ingredients_keeps_them(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(f"/api/cocktails/{self.mojito.id}/", {"name": "New name"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.mojito.cocktail_ingredients.count(), 2)

    def test_other_user_cant_update_or_delete(self):
        self.client.force_authenticate(self.other_user)

        response = self.client.patch(f"/api/cocktails/{self.mojito.id}/", {"name": "hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.delete(f"/api/cocktails/{self.mojito.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_any_cocktail(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(f"/api/cocktails/{self.mojito.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cocktail.objects.filter(id=self.mojito.id).exists())

    def test_not_found(self):
        response = self.client.get("/api/cocktails/9999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CocktailFilterTests(BaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        virgin = Cocktail.objects.create(
            name="Virgin Mojito", category="highball", instructions="Mix it.", author=cls.other_user
        )
        CocktailIngredient.objects.create(cocktail=virgin, ingredient=cls.mint, amount=8, unit="leaf")
        CocktailIngredient.objects.create(cocktail=virgin, ingredient=cls.lime, amount=25, unit="ml")

        mule = Cocktail.objects.create(name="Moscow Mule", category="classic", instructions="Mix it.")
        CocktailIngredient.objects.create(cocktail=mule, ingredient=cls.vodka, amount=50, unit="ml")
        CocktailIngredient.objects.create(cocktail=mule, ingredient=cls.lime, amount=15, unit="ml")

    def get_names(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return [c["name"] for c in response.data["results"]]

    def test_non_alcoholic_with_mint(self):
        names = self.get_names("/api/cocktails/?alcoholic=false&ingredient=mint")
        self.assertEqual(names, ["Virgin Mojito"])

    def test_alcoholic(self):
        names = self.get_names("/api/cocktails/?alcoholic=true")
        self.assertEqual(names, ["Mojito", "Moscow Mule"])

    def test_cocktail_must_have_all_ingredients(self):
        names = self.get_names("/api/cocktails/?ingredient=lime,vodka")
        self.assertEqual(names, ["Moscow Mule"])

    def test_filter_by_author(self):
        names = self.get_names(f"/api/cocktails/?author={self.user.id}")
        self.assertEqual(names, ["Mojito"])

    def test_filter_by_category(self):
        names = self.get_names("/api/cocktails/?category=classic")
        self.assertEqual(names, ["Moscow Mule"])

    def test_ordering(self):
        names = self.get_names("/api/cocktails/?ordering=-name")
        self.assertEqual(names, ["Virgin Mojito", "Moscow Mule", "Mojito"])

    def test_search(self):
        names = self.get_names("/api/cocktails/?search=virgin")
        self.assertEqual(names, ["Virgin Mojito"])

    def test_pagination(self):
        response = self.client.get("/api/cocktails/?page_size=2")

        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNotNone(response.data["next"])

    def test_wrong_filter_values(self):
        for url in [
            "/api/cocktails/?alcoholic=maybe",
            "/api/cocktails/?category=xyz",
            "/api/cocktails/?author=abc",
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, url)


class ReviewTests(BaseTestCase):
    def test_add_review(self):
        self.client.force_authenticate(self.other_user)
        url = f"/api/cocktails/{self.mojito.id}/reviews/"
        response = self.client.post(url, {"rating": 5, "comment": "Very good"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"], "anna")

    def test_review_needs_login(self):
        response = self.client.post(f"/api/cocktails/{self.mojito.id}/reviews/", {"rating": 5})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rating_must_be_1_to_5(self):
        self.client.force_authenticate(self.other_user)
        url = f"/api/cocktails/{self.mojito.id}/reviews/"

        self.assertEqual(self.client.post(url, {"rating": 0}).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.client.post(url, {"rating": 6}).status_code, status.HTTP_400_BAD_REQUEST)

    def test_only_one_review_per_user(self):
        Review.objects.create(cocktail=self.mojito, user=self.other_user, rating=4)
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f"/api/cocktails/{self.mojito.id}/reviews/", {"rating": 5})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_reviews_and_avg_rating(self):
        Review.objects.create(cocktail=self.mojito, user=self.user, rating=5)
        Review.objects.create(cocktail=self.mojito, user=self.other_user, rating=2)

        response = self.client.get(f"/api/cocktails/{self.mojito.id}/reviews/")
        self.assertEqual(response.data["count"], 2)

        response = self.client.get(f"/api/cocktails/{self.mojito.id}/")
        self.assertEqual(response.data["avg_rating"], 3.5)
