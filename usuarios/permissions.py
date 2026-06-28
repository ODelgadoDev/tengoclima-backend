from rest_framework.permissions import BasePermission, SAFE_METHODS


class EsDueno(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'perfilusuario')
            and request.user.perfilusuario.rol == 'DUENO'
            and request.user.perfilusuario.activo
        )


class EsAdministradorODueno(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'perfilusuario')
            and request.user.perfilusuario.rol in ['DUENO', 'ADMINISTRADOR']
            and request.user.perfilusuario.activo
        )


class EsUsuarioActivo(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'perfilusuario')
            and request.user.perfilusuario.activo
        )


class EsLecturaOAdministrador(BasePermission):
    """
    GET, HEAD, OPTIONS:
        Permitido para cualquier usuario activo.

    POST, PUT, PATCH, DELETE:
        Permitido solo para DUENO o ADMINISTRADOR.
    """

    def has_permission(self, request, view):
        if not (
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'perfilusuario')
            and request.user.perfilusuario.activo
        ):
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.perfilusuario.rol in ['DUENO', 'ADMINISTRADOR']