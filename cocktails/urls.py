from rest_framework.routers import DefaultRouter

from .views import CocktailViewSet, IngredientViewSet

router = DefaultRouter()
router.register("cocktails", CocktailViewSet, basename="cocktail")
router.register("ingredients", IngredientViewSet, basename="ingredient")

urlpatterns = router.urls
