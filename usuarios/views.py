from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import PerfilUsuario
from .serializers import PerfilUsuarioSerializer


class PerfilActualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil, created = PerfilUsuario.objects.get_or_create(
            usuario=request.user
        )

        serializer = PerfilUsuarioSerializer(perfil)
        return Response(serializer.data)