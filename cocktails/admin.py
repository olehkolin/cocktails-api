from django.contrib import admin

from .models import Cocktail, CocktailIngredient, Ingredient, Review


class CocktailIngredientInline(admin.TabularInline):
    model = CocktailIngredient
    extra = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ["name", "is_alcoholic"]
    list_filter = ["is_alcoholic"]
    search_fields = ["name"]


@admin.register(Cocktail)
class CocktailAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "author", "created_at"]
    list_filter = ["category"]
    search_fields = ["name"]
    inlines = [CocktailIngredientInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["cocktail", "user", "rating", "created_at"]
