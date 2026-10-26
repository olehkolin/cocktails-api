from django.core.management.base import BaseCommand

from cocktails.models import Cocktail, CocktailIngredient, Ingredient

# some test data, run: python manage.py seed

INGREDIENTS = [
    ("White rum", "Light rum", True),
    ("Vodka", "", True),
    ("Tequila", "", True),
    ("Triple sec", "Orange liqueur", True),
    ("Lime juice", "Fresh lime juice", False),
    ("Sugar syrup", "Sugar and water 1:1", False),
    ("Mint", "Fresh mint leaves", False),
    ("Soda water", "", False),
    ("Ginger beer", "Non-alcoholic", False),
    ("Cranberry juice", "", False),
]

COCKTAILS = [
    {
        "name": "Mojito",
        "category": "highball",
        "instructions": "Muddle mint with syrup and lime juice, add rum and ice, top with soda.",
        "ingredients": [
            ("White rum", 50, "ml"),
            ("Lime juice", 25, "ml"),
            ("Sugar syrup", 20, "ml"),
            ("Mint", 8, "leaf"),
            ("Soda water", 60, "ml"),
        ],
    },
    {
        "name": "Virgin Mojito",
        "category": "highball",
        "instructions": "Same as Mojito but without rum.",
        "ingredients": [
            ("Lime juice", 25, "ml"),
            ("Sugar syrup", 20, "ml"),
            ("Mint", 8, "leaf"),
            ("Soda water", 120, "ml"),
        ],
    },
    {
        "name": "Moscow Mule",
        "category": "highball",
        "instructions": "Pour everything over ice in a copper mug.",
        "ingredients": [
            ("Vodka", 50, "ml"),
            ("Lime juice", 15, "ml"),
            ("Ginger beer", 120, "ml"),
        ],
    },
    {
        "name": "Margarita",
        "category": "sour",
        "instructions": "Shake with ice and strain into a glass with salt rim.",
        "ingredients": [
            ("Tequila", 50, "ml"),
            ("Triple sec", 20, "ml"),
            ("Lime juice", 25, "ml"),
        ],
    },
    {
        "name": "Cosmopolitan",
        "category": "classic",
        "instructions": "Shake with ice and strain into a cocktail glass.",
        "ingredients": [
            ("Vodka", 40, "ml"),
            ("Triple sec", 15, "ml"),
            ("Cranberry juice", 30, "ml"),
            ("Lime juice", 15, "ml"),
        ],
    },
]


class Command(BaseCommand):
    help = "Adds some test ingredients and cocktails"

    def handle(self, *args, **options):
        for name, description, is_alcoholic in INGREDIENTS:
            Ingredient.objects.get_or_create(
                name=name,
                defaults={"description": description, "is_alcoholic": is_alcoholic},
            )

        for data in COCKTAILS:
            cocktail, created = Cocktail.objects.get_or_create(
                name=data["name"],
                defaults={"category": data["category"], "instructions": data["instructions"]},
            )
            if not created:
                continue
            for ingredient_name, amount, unit in data["ingredients"]:
                CocktailIngredient.objects.create(
                    cocktail=cocktail,
                    ingredient=Ingredient.objects.get(name=ingredient_name),
                    amount=amount,
                    unit=unit,
                )

        self.stdout.write(self.style.SUCCESS("Test data added"))
