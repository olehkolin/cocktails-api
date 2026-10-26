from django.db.models import Avg, ProtectedError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .filters import CocktailFilter, IngredientFilter
from .models import Cocktail, Ingredient, Review
from .permissions import IngredientPermission, IsAuthorOrAdmin
from .serializers import CocktailSerializer, IngredientSerializer, ReviewSerializer


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IngredientPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = IngredientFilter
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def destroy(self, request, *args, **kwargs):
        ingredient = self.get_object()
        try:
            ingredient.delete()
        except ProtectedError:
            return Response(
                {"detail": "This ingredient is used in some cocktails, can't delete it."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class CocktailViewSet(viewsets.ModelViewSet):
    serializer_class = CocktailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CocktailFilter
    search_fields = ["name", "instructions"]
    ordering_fields = ["name", "category", "created_at", "avg_rating"]
    # default ordering, without it the list comes in random order (because of annotate)
    ordering = ["name"]

    def get_queryset(self):
        # prefetch_related so we don't do a separate query for every cocktail
        return (
            Cocktail.objects.select_related("author")
            .prefetch_related("cocktail_ingredients__ingredient")
            .annotate(avg_rating=Avg("reviews__rating"))
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    # GET  /api/cocktails/{id}/reviews/ - list of reviews
    # POST /api/cocktails/{id}/reviews/ - add review (logged in users)
    @action(detail=True, methods=["get", "post"], serializer_class=ReviewSerializer)
    def reviews(self, request, pk=None):
        # not using self.get_object() here, because IsAuthorOrAdmin would block
        # POST for everyone who is not the author
        cocktail = get_object_or_404(Cocktail, pk=pk)

        if request.method == "GET":
            reviews = cocktail.reviews.select_related("user")
            page = self.paginate_queryset(reviews)
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        if Review.objects.filter(cocktail=cocktail, user=request.user).exists():
            return Response(
                {"detail": "You already reviewed this cocktail."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cocktail=cocktail, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
