from rest_framework import viewsets

from .models import Cotizacion, ConceptoCotizacion
from .serializers import CotizacionSerializer, ConceptoCotizacionSerializer
from usuarios.permissions import EsLecturaOAdministrador


class CotizacionViewSet(viewsets.ModelViewSet):
    queryset = (
        Cotizacion.objects
        .select_related('cliente')
        .prefetch_related('conceptos', 'pagos')
        .order_by('-fecha_creacion')
    )
    serializer_class = CotizacionSerializer
    permission_classes = [EsLecturaOAdministrador]

    search_fields = [
        'codigo',
        'descripcion',
        'cliente__nombre_solicitante',
        'cliente__empresa',
    ]

    filterset_fields = [
        'estado',
        'tipo',
        'cliente',
    ]

    ordering_fields = [
        'codigo',
        'subtotal',
        'iva',
        'total',
        'estado',
        'fecha_creacion',
        'fecha_actualizacion',
    ]


class ConceptoCotizacionViewSet(viewsets.ModelViewSet):
    queryset = (
        ConceptoCotizacion.objects
        .select_related('cotizacion', 'cotizacion__cliente')
        .order_by('id')
    )
    serializer_class = ConceptoCotizacionSerializer
    permission_classes = [EsLecturaOAdministrador]

    search_fields = [
        'descripcion',
        'cotizacion__codigo',
    ]

    filterset_fields = [
        'cotizacion',
        'unidad',
    ]

    ordering_fields = [
        'descripcion',
        'cantidad',
        'precio_unitario',
        'total',
    ]