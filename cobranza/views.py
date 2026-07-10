from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Pago
from .serializers import PagoSerializer, PagoDetalleSerializer
from cotizaciones.models import Cotizacion
from usuarios.permissions import EsUsuarioActivo, EsLecturaOAdministrador
from core.viewsets import BaseModelViewSet


class PagoViewSet(BaseModelViewSet):
    queryset = (
        Pago.objects
        .select_related('cotizacion', 'cotizacion__cliente')
        .order_by('-fecha_pago', '-fecha_creacion')
    )
    serializer_class = PagoSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PagoDetalleSerializer

        return PagoSerializer

    search_fields = [
        'referencia',
        'notas',
        'cotizacion__codigo',
        'cotizacion__descripcion',
        'cotizacion__cliente__nombre_solicitante',
        'cotizacion__cliente__empresa',
    ]

    filterset_fields = [
        'cotizacion',
        'metodo_pago',
        'fecha_pago',
    ]

    ordering_fields = [
        'monto',
        'metodo_pago',
        'fecha_pago',
        'fecha_creacion',
    ]


class PorCobrarView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        data = []

        cotizaciones = (
            Cotizacion.objects
            .select_related('cliente')
            .prefetch_related('pagos')
            .order_by('-fecha_creacion')
        )

        for cotizacion in cotizaciones:
            if cotizacion.saldo_pendiente > 0:
                data.append({
                    'id': cotizacion.id,
                    'codigo': cotizacion.codigo,
                    'cliente': cotizacion.cliente.nombre_solicitante,
                    'empresa': cotizacion.cliente.empresa,
                    'total': cotizacion.total,
                    'pagado': cotizacion.total_pagado,
                    'pendiente': cotizacion.saldo_pendiente,
                    'estado': cotizacion.estado_cobranza,
                })

        return Response(data)


class PagadosView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        data = []

        cotizaciones = (
            Cotizacion.objects
            .select_related('cliente')
            .prefetch_related('pagos')
            .order_by('-fecha_creacion')
        )

        for cotizacion in cotizaciones:
            if cotizacion.estado_cobranza == 'PAGADO':
                data.append({
                    'id': cotizacion.id,
                    'codigo': cotizacion.codigo,
                    'cliente': cotizacion.cliente.nombre_solicitante,
                    'empresa': cotizacion.cliente.empresa,
                    'total': cotizacion.total,
                    'pagado': cotizacion.total_pagado,
                })

        return Response(data)