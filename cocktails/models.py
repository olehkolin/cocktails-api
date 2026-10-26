from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_alcoholic = models.BooleanField(default=False)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Cocktail(models.Model):
    CATEGORY_CHOICES = [
        ("classic", "Classic"),
        ("sour", "Sour"),
        ("highball", "Highball"),
        ("tropical", "Tropical"),
        ("shot", "Shot"),
        ("hot", "Hot drink"),
        ("other", "Other"),
    ]

    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    instructions = models.TextField()
    # if the user gets deleted, the cocktail stays (just without author)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cocktails",
    )
    ingredients = models.ManyToManyField(
        Ingredient, through="CocktailIngredient", related_name="cocktails"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# extra table for M2M because we need to store amount and unit
class CocktailIngredient(models.Model):
    UNIT_CHOICES = [
        ("ml", "ml"),
        ("cl", "cl"),
        ("oz", "oz"),
        ("g", "g"),
        ("tsp", "teaspoon"),
        ("tbsp", "tablespoon"),
        ("dash", "dash"),
        ("piece", "piece"),
        ("slice", "slice"),
        ("leaf", "leaf"),
    ]

    cocktail = models.ForeignKey(
        Cocktail, on_delete=models.CASCADE, related_name="cocktail_ingredients"
    )
    # PROTECT - can't delete an ingredient that is used in some cocktail
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name="cocktail_ingredients"
    )
    amount = models.DecimalField(
        max_digits=7, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cocktail", "ingredient"], name="unique_cocktail_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.cocktail} - {self.ingredient} ({self.amount} {self.unit})"


class Review(models.Model):
    cocktail = models.ForeignKey(Cocktail, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        # one review per user for one cocktail
        constraints = [
            models.UniqueConstraint(fields=["cocktail", "user"], name="unique_review")
        ]

    def __str__(self):
        return f"{self.user} - {self.cocktail} ({self.rating})"
