from .models import ClientePotencial
from .serializers import (
    ClientePotencialSerializer,
    ClientePotencialDetalleSerializer
)
from usuarios.permissions import EsLecturaOAdministrador
from core.viewsets import BaseModelViewSet


class ClientePotencialViewSet(BaseModelViewSet):
    queryset = ClientePotencial.objects.all().order_by('-fecha_creacion')
    serializer_class = ClientePotencialSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClientePotencialDetalleSerializer

        return ClientePotencialSerializer

    search_fields = [
        'nombre_solicitante',
        'empresa',
        'telefono',
        'direccion',
        'descripcion',
    ]

    filterset_fields = [
        'estado',
    ]

    ordering_fields = [
        'nombre_solicitante',
        'empresa',
        'estado',
        'fecha_creacion',
        'fecha_actualizacion',
    ]