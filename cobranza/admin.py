from django.contrib import admin

from core.admin import AuditableAdmin

from .models import FacturaDocumento, Pago


@admin.register(FacturaDocumento)
class FacturaDocumentoAdmin(AuditableAdmin):
    list_display = (
        "folio",
        "cotizacion",
        "importe",
        "fecha_emision",
        "estado",
        "fecha_pago",
    )
    list_filter = (
        "estado",
        "fecha_emision",
        "fecha_pago",
    )
    search_fields = (
        "folio",
        "cotizacion__codigo",
        "cotizacion__cliente__nombre_solicitante",
        "cotizacion__cliente__empresa",
        "observaciones",
    )
    ordering = ("-fecha_emision", "-fecha_creacion")
    readonly_fields = ("estado", "fecha_pago")


@admin.register(Pago)
class PagoAdmin(AuditableAdmin):
    list_display = (
        "cotizacion",
        "factura",
        "monto",
        "metodo_pago",
        "referencia",
        "fecha_pago",
    )
    list_filter = (
        "metodo_pago",
        "fecha_pago",
    )
    search_fields = (
        "cotizacion__codigo",
        "cotizacion__descripcion",
        "cotizacion__cliente__nombre_solicitante",
        "cotizacion__cliente__empresa",
        "factura__folio",
        "referencia",
        "notas",
    )
    ordering = ("-fecha_pago", "-fecha_creacion")
