from rest_framework import viewsets

from .models import CategoriaGasto, Gasto
from .serializers import (
    CategoriaGastoSerializer,
    GastoSerializer,
    GastoDetalleSerializer
)

from usuarios.permissions import EsLecturaOAdministrador
from core.viewsets import BaseModelViewSet


class CategoriaGastoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaGasto.objects.all().order_by('nombre')
    serializer_class = CategoriaGastoSerializer
    permission_classes = [EsLecturaOAdministrador]

    search_fields = [
        'nombre',
        'descripcion',
    ]

    filterset_fields = [
        'activo',
    ]

    ordering_fields = [
        'nombre',
        'activo',
    ]


class GastoViewSet(BaseModelViewSet):
    queryset = (
        Gasto.objects
        .select_related('categoria')
        .order_by('-fecha_gasto')
    )
    serializer_class = GastoSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GastoDetalleSerializer

        return GastoSerializer

    search_fields = [
        'concepto',
        'proveedor',
        'notas',
        'categoria__nombre',
    ]

    filterset_fields = [
        'categoria',
        'metodo_pago',
        'fecha_gasto',
    ]

    ordering_fields = [
        'concepto',
        'proveedor',
        'monto',
        'metodo_pago',
        'fecha_gasto',
        'fecha_creacion',
    ]