from django.urls import path

from .views import PerfilActualView, UsuariosActivosView


urlpatterns = [
    path(
        "perfil/",
        PerfilActualView.as_view(),
        name="perfil-actual",
    ),
    path(
        "usuarios/",
        UsuariosActivosView.as_view(),
        name="usuarios-activos",
    ),
]
