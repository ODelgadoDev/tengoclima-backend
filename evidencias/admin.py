from django.contrib import admin

from core.admin import AuditableAdmin

from .models import Evidencia


@admin.register(Evidencia)
class EvidenciaAdmin(AuditableAdmin):
    list_display = (
        "id",
        "tipo",
        "origen_admin",
        "nombre_original",
        "extension",
        "tamanio_legible",
        "fecha_creacion",
    )
    list_filter = (
        "tipo",
        "extension",
        "activo",
        "eliminado",
    )
    search_fields = (
        "descripcion",
        "nombre_original",
        "cotizacion__codigo",
        "cotizacion__cliente__nombre_solicitante",
        "cotizacion__cliente__empresa",
        "proyecto__nombre",
        "proyecto__cliente__nombre_solicitante",
        "proyecto__cliente__empresa",
    )
    ordering = ("-fecha_creacion",)
    readonly_fields = (
        "nombre_original",
        "extension",
        "mime_type",
        "tamanio_bytes",
    )
    fieldsets = (
        (
            "Origen",
            {
                "fields": (
                    "cotizacion",
                    "proyecto",
                    "tipo",
                ),
            },
        ),
        (
            "Archivo",
            {
                "fields": (
                    "archivo",
                    "descripcion",
                    "nombre_original",
                    "extension",
                    "mime_type",
                    "tamanio_bytes",
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

    @admin.display(description="Origen")
    def origen_admin(self, obj):
        if obj.cotizacion_id:
            return f"Cotización {obj.cotizacion.codigo}"
        if obj.proyecto_id:
            return f"Proyecto {obj.proyecto.nombre}"
        return "Sin origen"

    @admin.display(description="Tamaño")
    def tamanio_legible(self, obj):
        tamanio = obj.tamanio_bytes or 0
        if tamanio >= 1024 * 1024:
            return f"{tamanio / (1024 * 1024):.2f} MB"
        if tamanio >= 1024:
            return f"{tamanio / 1024:.2f} KB"
        return f"{tamanio} B"
