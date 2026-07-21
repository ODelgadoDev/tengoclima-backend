from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PerfilUsuario
from .permissions import EsUsuarioActivo
from .serializers import (
    PerfilUsuarioSerializer,
    UsuarioResponsableSerializer,
)


class PerfilActualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil, created = PerfilUsuario.objects.get_or_create(
            usuario=request.user,
        )
        serializer = PerfilUsuarioSerializer(perfil)
        return Response(serializer.data)


class UsuariosActivosView(ListAPIView):
    """
    Lista ligera y sin paginación para selectores de responsables.
    """

    serializer_class = UsuarioResponsableSerializer
    permission_classes = [EsUsuarioActivo]
    pagination_class = None

    def get_queryset(self):
        return (
            PerfilUsuario.objects
            .select_related("usuario")
            .filter(
                activo=True,
                usuario__is_active=True,
            )
            .order_by(
                "usuario__first_name",
                "usuario__last_name",
                "usuario__username",
            )
        )
