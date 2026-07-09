from .models import ClientePotencial
from .serializers import ClientePotencialSerializer
from usuarios.permissions import EsLecturaOAdministrador
from core.viewsets import BaseModelViewSet


class ClientePotencialViewSet(BaseModelViewSet):
    queryset = ClientePotencial.objects.all().order_by('-fecha_creacion')
    serializer_class = ClientePotencialSerializer
    permission_classes = [EsLecturaOAdministrador]

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