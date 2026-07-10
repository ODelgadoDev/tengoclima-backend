from .models import Evidencia
from .serializers import EvidenciaSerializer
from usuarios.permissions import EsLecturaOAdministrador
from core.viewsets import BaseModelViewSet


class EvidenciaViewSet(BaseModelViewSet):
    queryset = (
        Evidencia.objects
        .select_related('cotizacion', 'cotizacion__cliente')
        .order_by('-fecha_creacion')
    )
    serializer_class = EvidenciaSerializer
    permission_classes = [EsLecturaOAdministrador]

    search_fields = [
        'descripcion',
        'cotizacion__codigo',
        'cotizacion__cliente__nombre_solicitante',
        'cotizacion__cliente__empresa',
    ]

    filterset_fields = [
        'cotizacion',
        'activo',
        'eliminado',
    ]

    ordering_fields = [
        'fecha_creacion',
        'fecha_actualizacion',
    ]