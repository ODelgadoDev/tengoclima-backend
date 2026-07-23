from django.contrib import admin

from core.admin import AuditableAdmin

from .models import Proyecto


@admin.register(Proyecto)
class ProyectoAdmin(AuditableAdmin):
    list_display = (
        "nombre",
        "cliente",
        "responsable",
        "estado",
        "cantidad_cotizaciones",
        "estado_facturacion",
        "estado_cobranza",
        "fecha_inicio",
        "fecha_fin_estimada",
        "fecha_fin_real",
    )
    list_filter = (
        "estado",
        "fecha_inicio",
        "fecha_fin_estimada",
    )
    search_fields = (
        "nombre",
        "cliente__nombre_solicitante",
        "cliente__empresa",
        "cotizaciones__codigo",
        "responsable__username",
        "responsable__first_name",
        "responsable__last_name",
    )
    ordering = ("-fecha_creacion",)
    fieldsets = (
        (
            "Información del proyecto",
            {
                "fields": (
                    "cliente",
                    "nombre",
                    "responsable",
                    "estado",
                    "notas",
                ),
            },
        ),
        (
            "Fechas",
            {
                "fields": (
                    "fecha_inicio",
                    "fecha_fin_estimada",
                    "fecha_fin_real",
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

    @admin.display(description="Cotizaciones")
    def cantidad_cotizaciones(self, obj):
        return obj.cotizaciones.count()
