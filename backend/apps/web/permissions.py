from rest_framework import permissions


class IsAdminUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # Allow read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the admin user
        return request.user.is_staff or request.user.role == 'admin_role'
