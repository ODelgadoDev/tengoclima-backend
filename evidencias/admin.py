from django.contrib import admin

from .models import Evidencia


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cotizacion',
        'descripcion',
        'activo',
        'eliminado',
        'fecha_creacion',
    )

    list_filter = (
        'activo',
        'eliminado',
        'fecha_creacion',
    )

    search_fields = (
        'descripcion',
        'cotizacion__codigo',
        'cotizacion__cliente__nombre_solicitante',
        'cotizacion__cliente__empresa',
    )

    readonly_fields = (
        'creado_por',
        'modificado_por',
        'fecha_creacion',
        'fecha_actualizacion',
    )