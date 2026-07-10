from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """Allow access if the note belongs to the request user, or user is admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.profile.is_admin:
            return True
        return obj.user == request.user
