from django.contrib import admin

from core.admin import AuditableAdmin

from .models import CategoriaGasto, Gasto


@admin.register(CategoriaGasto)
class CategoriaGastoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "descripcion")
    ordering = ("nombre",)


@admin.register(Gasto)
class GastoAdmin(AuditableAdmin):
    list_display = (
        "concepto",
        "categoria",
        "proyecto",
        "cotizacion",
        "proveedor",
        "monto",
        "iva",
        "metodo_pago",
        "fecha_gasto",
    )
    list_filter = (
        "categoria",
        "proyecto",
        "metodo_pago",
        "fecha_gasto",
    )
    search_fields = (
        "concepto",
        "proveedor",
        "categoria__nombre",
        "proyecto__nombre",
        "cotizacion__codigo",
        "notas",
    )
    ordering = ("-fecha_gasto", "-fecha_creacion")
    fieldsets = (
        (
            "Información del gasto",
            {
                "fields": (
                    "categoria",
                    "proyecto",
                    "cotizacion",
                    "concepto",
                    "proveedor",
                    "monto",
                    "iva",
                    "metodo_pago",
                    "comprobante",
                    "notas",
                    "fecha_gasto",
                ),
            },
        ),
        (
            "Auditoría",
            {
                "classes": ("collapse",),
                "fields": (
                    "activo",
                    "eliminado",
                    "creado_por",
                    "modificado_por",
                    "fecha_creacion",
                    "fecha_actualizacion",
                ),
            },
        ),
    )
