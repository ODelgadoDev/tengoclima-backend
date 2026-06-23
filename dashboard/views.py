from rest_framework.views import APIView
from rest_framework.response import Response

from clientes.models import ClientePotencial
from cotizaciones.models import Cotizacion
from proyectos.models import Proyecto
from contabilidad.models import Gasto


class DashboardResumenView(APIView):

    def get(self, request):
        clientes = ClientePotencial.objects.count()
        cotizaciones = Cotizacion.objects.count()
        proyectos = Proyecto.objects.count()

        monto_cobrado = 0
        monto_por_cobrar = 0

        for cotizacion in Cotizacion.objects.all():
            monto_cobrado += cotizacion.total_pagado
            monto_por_cobrar += cotizacion.saldo_pendiente

        data = {
            'clientes': clientes,
            'cotizaciones': cotizaciones,
            'proyectos': proyectos,
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

    def get(self, request):
        monto_cobrado = 0
        monto_por_cobrar = 0

        for cotizacion in Cotizacion.objects.all():
            monto_cobrado += cotizacion.total_pagado
            monto_por_cobrar += cotizacion.saldo_pendiente

        total_gastos = sum(gasto.monto for gasto in Gasto.objects.all())
        utilidad = monto_cobrado - total_gastos

        data = {
            'monto_cobrado': monto_cobrado,
            'monto_por_cobrar': monto_por_cobrar,
            'total_gastos': total_gastos,
            'utilidad': utilidad,
        }

        return Response(data)