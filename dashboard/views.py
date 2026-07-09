from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response

from clientes.models import ClientePotencial
from cotizaciones.models import Cotizacion
from proyectos.models import Proyecto
from contabilidad.models import Gasto

from usuarios.permissions import EsUsuarioActivo


class DashboardResumenView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        cotizaciones = (
            Cotizacion.objects
            .prefetch_related('pagos')
            .all()
        )

        monto_cobrado = 0
        monto_por_cobrar = 0

        for cotizacion in cotizaciones:
            monto_cobrado += cotizacion.total_pagado
            monto_por_cobrar += cotizacion.saldo_pendiente

        data = {
            'clientes': ClientePotencial.objects.count(),
            'cotizaciones': Cotizacion.objects.count(),
            'proyectos': Proyecto.objects.count(),
            'monto_cobrado': monto_cobrado,
            'monto_por_cobrar': monto_por_cobrar,
            'cotizaciones_pendientes': Cotizacion.objects.filter(
                estado=Cotizacion.ESTADO_PENDIENTE
            ).count(),
            'cotizaciones_autorizadas': Cotizacion.objects.filter(
                estado=Cotizacion.ESTADO_AUTORIZADA
            ).count(),
            'cotizaciones_rechazadas': Cotizacion.objects.filter(
                estado=Cotizacion.ESTADO_RECHAZADA
            ).count(),
        }

        return Response(data)


class DashboardFinanzasView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        cotizaciones = (
            Cotizacion.objects
            .prefetch_related('pagos')
            .all()
        )

        monto_cobrado = 0
        monto_por_cobrar = 0

        for cotizacion in cotizaciones:
            monto_cobrado += cotizacion.total_pagado
            monto_por_cobrar += cotizacion.saldo_pendiente

        total_gastos = Gasto.objects.aggregate(
            total=Sum('monto')
        )['total'] or 0

        utilidad = monto_cobrado - total_gastos

        data = {
            'monto_cobrado': monto_cobrado,
            'monto_por_cobrar': monto_por_cobrar,
            'total_gastos': total_gastos,
            'utilidad': utilidad,
        }

        return Response(data)