from decimal import Decimal

from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from clientes.models import ClientePotencial
from cobranza.models import FacturaDocumento
from contabilidad.models import Gasto
from cotizaciones.models import Cotizacion
from proyectos.models import Proyecto
from usuarios.permissions import EsUsuarioActivo


class DashboardResumenView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        cotizaciones = (
            Cotizacion.objects
            .prefetch_related("pagos", "facturas")
            .all()
        )

        monto_cobrado = Decimal("0.00")
        monto_por_cobrar = Decimal("0.00")
        monto_facturado = Decimal("0.00")
        monto_pendiente_facturar = Decimal("0.00")

        for cotizacion in cotizaciones:
            monto_cobrado += cotizacion.total_pagado
            monto_por_cobrar += cotizacion.saldo_pendiente
            monto_facturado += cotizacion.total_facturado
            monto_pendiente_facturar += cotizacion.saldo_por_facturar

        data = {
            "clientes": ClientePotencial.objects.count(),
            "cotizaciones": Cotizacion.objects.count(),
            "proyectos": Proyecto.objects.count(),
            "monto_cobrado": monto_cobrado,
            "monto_por_cobrar": monto_por_cobrar,
            "monto_facturado": monto_facturado,
            "monto_pendiente_facturar": monto_pendiente_facturar,
            "facturas": FacturaDocumento.objects.count(),
            "facturas_pendientes": FacturaDocumento.objects.filter(
                estado=FacturaDocumento.ESTADO_PENDIENTE,
            ).count(),
            "facturas_pagadas": FacturaDocumento.objects.filter(
                estado=FacturaDocumento.ESTADO_PAGADA,
            ).count(),
            "cotizaciones_pendientes": Cotizacion.objects.filter(
                estado=Cotizacion.ESTADO_PENDIENTE,
            ).count(),
            "cotizaciones_autorizadas": Cotizacion.objects.filter(
                estado=Cotizacion.ESTADO_AUTORIZADA,
            ).count(),
            "cotizaciones_canceladas": Cotizacion.objects.filter(
                estado=Cotizacion.ESTADO_CANCELADA,
            ).count(),
        }

        return Response(data)


class DashboardFinanzasView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        cotizaciones = (
            Cotizacion.objects
            .prefetch_related("pagos", "facturas")
            .all()
        )

        monto_cobrado = Decimal("0.00")
        monto_por_cobrar = Decimal("0.00")
        monto_facturado = Decimal("0.00")
        monto_pendiente_facturar = Decimal("0.00")

        for cotizacion in cotizaciones:
            monto_cobrado += cotizacion.total_pagado
            monto_por_cobrar += cotizacion.saldo_pendiente
            monto_facturado += cotizacion.total_facturado
            monto_pendiente_facturar += cotizacion.saldo_por_facturar

        total_gastos = Gasto.objects.aggregate(total=Sum("monto"))["total"] or 0
        utilidad = monto_cobrado - total_gastos

        data = {
            "monto_cobrado": monto_cobrado,
            "monto_por_cobrar": monto_por_cobrar,
            "monto_facturado": monto_facturado,
            "monto_pendiente_facturar": monto_pendiente_facturar,
            "total_gastos": total_gastos,
            "utilidad": utilidad,
        }

        return Response(data)
