from django_filters import rest_framework as filters

from .models import Cocktail, Ingredient

# used ChoiceFilter instead of BooleanFilter, because BooleanFilter
# just ignores wrong values (like ?alcoholic=abc) and I wanted a 400 error
YES_NO = [("true", "true"), ("false", "false")]


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    is_alcoholic = filters.ChoiceFilter(choices=YES_NO, method="filter_is_alcoholic")

    class Meta:
        model = Ingredient
        fields = ["name", "is_alcoholic"]

    def filter_is_alcoholic(self, queryset, name, value):
        return queryset.filter(is_alcoholic=(value == "true"))


class CocktailFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")
    category = filters.ChoiceFilter(choices=Cocktail.CATEGORY_CHOICES)
    author = filters.NumberFilter(field_name="author_id")
    alcoholic = filters.ChoiceFilter(choices=YES_NO, method="filter_alcoholic")
    # ?ingredient=mint or ?ingredient=mint,lime (cocktail must have all of them)
    ingredient = filters.CharFilter(method="filter_ingredient")

    class Meta:
        model = Cocktail
        fields = ["name", "category", "author", "alcoholic", "ingredient"]

    def filter_alcoholic(self, queryset, name, value):
        if value == "true":
            return queryset.filter(ingredients__is_alcoholic=True).distinct()
        # non-alcoholic = no alcoholic ingredient at all
        return queryset.exclude(ingredients__is_alcoholic=True)

    def filter_ingredient(self, queryset, name, value):
        names = [n.strip() for n in value.split(",") if n.strip()]
        for ingredient_name in names:
            queryset = queryset.filter(ingredients__name__icontains=ingredient_name)
        return queryset.distinct()
