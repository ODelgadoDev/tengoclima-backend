from core.viewsets import BaseModelViewSet
from usuarios.permissions import EsLecturaOAdministrador

from .models import ClientePotencial
from .serializers import (
    ClientePotencialDetalleSerializer,
    ClientePotencialSerializer,
)


class ClientePotencialViewSet(BaseModelViewSet):
    queryset = ClientePotencial.objects.all().order_by("-fecha_creacion")
    serializer_class = ClientePotencialSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ClientePotencialDetalleSerializer
        return ClientePotencialSerializer

    search_fields = [
        "nombre_solicitante",
        "empresa",
        "telefono",
        "direccion",
        "descripcion",
    ]
    ordering_fields = [
        "nombre_solicitante",
        "empresa",
        "fecha_creacion",
        "fecha_actualizacion",
    ]
