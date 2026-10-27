from django.db import transaction
from rest_framework import serializers

from .models import Cocktail, CocktailIngredient, Ingredient, Review


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name", "description", "is_alcoholic", "image_url", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate_name(self, value):
        # "Mint" and "mint" should be treated as the same ingredient
        if Ingredient.objects.filter(name__iexact=value).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("Ingredient with this name already exists.")
        return value


class CocktailIngredientSerializer(serializers.ModelSerializer):
    # when creating a cocktail you send ingredient_id, in response you also get the name
    ingredient_id = serializers.PrimaryKeyRelatedField(
        source="ingredient", queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    is_alcoholic = serializers.BooleanField(source="ingredient.is_alcoholic", read_only=True)

    class Meta:
        model = CocktailIngredient
        fields = ["ingredient_id", "name", "is_alcoholic", "amount", "unit"]


class CocktailSerializer(serializers.ModelSerializer):
    ingredients = CocktailIngredientSerializer(source="cocktail_ingredients", many=True)
    author = serializers.CharField(source="author.username", read_only=True)
    is_alcoholic = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Cocktail
        fields = [
            "id",
            "name",
            "category",
            "instructions",
            "is_alcoholic",
            "avg_rating",
            "author",
            "ingredients",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_is_alcoholic(self, obj) -> bool:
        for item in obj.cocktail_ingredients.all():
            if item.ingredient.is_alcoholic:
                return True
        return False

    def get_avg_rating(self, obj) -> float | None:
        # avg_rating comes from annotate() in the view
        avg = getattr(obj, "avg_rating", None)
        if avg is None:
            return None
        return round(avg, 1)

    def validate_ingredients(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("Cocktail must have at least one ingredient.")

        ids = [item["ingredient"].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("The same ingredient was added twice.")
        return value

    # atomic - if something fails, nothing is saved
    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop("cocktail_ingredients")
        cocktail = Cocktail.objects.create(**validated_data)
        for item in ingredients_data:
            CocktailIngredient.objects.create(cocktail=cocktail, **item)
        return cocktail

    @transaction.atomic
    def update(self, instance, validated_data):
        # with PATCH ingredients can be skipped, then we don't touch them
        ingredients_data = validated_data.pop("cocktail_ingredients", None)

        instance.name = validated_data.get("name", instance.name)
        instance.category = validated_data.get("category", instance.category)
        instance.instructions = validated_data.get("instructions", instance.instructions)
        instance.save()

        if ingredients_data is not None:
            # easiest way - remove old ones and add again
            instance.cocktail_ingredients.all().delete()
            for item in ingredients_data:
                CocktailIngredient.objects.create(cocktail=instance, **item)

        return instance


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "user", "rating", "comment", "created_at"]
        read_only_fields = ["created_at"]
