from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CambiarContrasenaView,
    PerfilActualView,
    RegistroActividadListView,
    UsuarioAdministracionViewSet,
    UsuariosActivosView,
)


router = DefaultRouter()
router.register(
    r"administracion-usuarios",
    UsuarioAdministracionViewSet,
    basename="administracion-usuarios",
)

urlpatterns = [
    path(
        "perfil/",
        PerfilActualView.as_view(),
        name="perfil-actual",
    ),
    path(
        "perfil/cambiar-contrasena/",
        CambiarContrasenaView.as_view(),
        name="cambiar-contrasena",
    ),
    path(
        "usuarios/",
        UsuariosActivosView.as_view(),
        name="usuarios-activos",
    ),
    path(
        "actividad/",
        RegistroActividadListView.as_view(),
        name="registro-actividad",
    ),
    path("", include(router.urls)),
]
