from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Pago
from .serializers import PagoSerializer

from cotizaciones.models import Cotizacion


class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all().order_by('-fecha_pago', '-fecha_creacion')
    serializer_class = PagoSerializer


class PorCobrarView(APIView):

    def get(self, request):

        data = []

        for cotizacion in Cotizacion.objects.all():

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

    def get(self, request):

        data = []

        for cotizacion in Cotizacion.objects.all():

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