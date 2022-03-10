from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user.is_authenticated:

            return user.is_admin or user.is_superuser

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user.is_authenticated:
            return user.is_admin or user.is_superuser


class IsAuthorAdminModeratorOrReadOnly(BasePermission):

    def has_object_permission(self, request, view, obj):
        return bool(
            obj.author == request.user
            or request.method in SAFE_METHODS
            or request.auth and request.user.is_admin
            or request.auth and request.user.is_moderator
        )


class AdminPermission(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if user.is_authenticated:
            return user.is_admin or user.is_superuser

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_authenticated:
            return user.is_admin or user.is_superuser
