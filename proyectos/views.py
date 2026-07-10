from .models import Proyecto
from .serializers import (
    ProyectoSerializer,
    ProyectoDetalleSerializer
)
from usuarios.permissions import EsLecturaOAdministrador
from core.viewsets import BaseModelViewSet


class ProyectoViewSet(BaseModelViewSet):
    queryset = (
        Proyecto.objects
        .select_related('cotizacion', 'cotizacion__cliente', 'responsable')
        .order_by('-fecha_creacion')
    )
    serializer_class = ProyectoSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProyectoDetalleSerializer

        return ProyectoSerializer

    search_fields = [
        'nombre',
        'responsable__username',
        'responsable__first_name',
        'responsable__last_name',
        'notas',
        'cotizacion__codigo',
        'cotizacion__cliente__nombre_solicitante',
        'cotizacion__cliente__empresa',
    ]

    filterset_fields = [
        'estado',
        'responsable',
        'cotizacion',
    ]

    ordering_fields = [
        'nombre',
        'responsable',
        'fecha_inicio',
        'fecha_fin_estimada',
        'fecha_fin_real',
        'estado',
        'fecha_creacion',
        'fecha_actualizacion',
    ]