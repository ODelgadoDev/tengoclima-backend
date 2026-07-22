from rest_framework.permissions import BasePermission, SAFE_METHODS


def _perfil_activo(request):
    return (
        request.user
        and request.user.is_authenticated
        and request.user.is_active
        and hasattr(request.user, "perfilusuario")
        and request.user.perfilusuario.activo
    )


def _contrasena_actualizada(request):
    return not request.user.perfilusuario.requiere_cambio_contrasena


class EsPerfilActivo(BasePermission):
    """Permite consultar el perfil y cambiar la contraseña temporal."""

    def has_permission(self, request, view):
        return bool(_perfil_activo(request))


class EsDueno(BasePermission):
    def has_permission(self, request, view):
        return (
            _perfil_activo(request)
            and _contrasena_actualizada(request)
            and request.user.perfilusuario.rol == "DUENO"
        )


class EsAdministradorODueno(BasePermission):
    def has_permission(self, request, view):
        return (
            _perfil_activo(request)
            and _contrasena_actualizada(request)
            and request.user.perfilusuario.rol in ["DUENO", "ADMINISTRADOR"]
        )


class EsUsuarioActivo(BasePermission):
    def has_permission(self, request, view):
        return (
            _perfil_activo(request)
            and _contrasena_actualizada(request)
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
            _perfil_activo(request)
            and _contrasena_actualizada(request)
        ):
            return False

        if request.method in SAFE_METHODS:
            return True

        return request.user.perfilusuario.rol in ["DUENO", "ADMINISTRADOR"]
