from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAdmin(BasePermission):
    """Everyone can read, but only the author or admin can edit / delete."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_admin


class IngredientPermission(BasePermission):
    """
    Read - everyone
    Add - logged in users (so they can add missing ingredient for their cocktail)
    Edit / delete - only admin, because ingredient can be used in other people's cocktails
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user.is_authenticated:
            return False
        if request.method == "POST":
            return True
        return request.user.is_admin
