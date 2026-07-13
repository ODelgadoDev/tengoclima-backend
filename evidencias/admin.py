from django.contrib import admin

from .models import Evidencia
from core.admin import AuditableAdmin


@admin.register(Evidencia)
class EvidenciaAdmin(AuditableAdmin):
    list_display = (
        'id',
        'cotizacion',
        'descripcion',
    )

    list_filter = ()

    search_fields = (
        'descripcion',
        'cotizacion__codigo',
        'cotizacion__cliente__nombre_solicitante',
        'cotizacion__cliente__empresa',
    )

    ordering = (
        '-fecha_creacion',
    )

    fieldsets = (
        (
            'Información de la evidencia',
            {
                'fields': (
                    'cotizacion',
                    'imagen',
                    'descripcion',
                )
            },
        ),
        (
            'Auditoría',
            {
                'classes': ('collapse',),
                'fields': (
                    'activo',
                    'eliminado',
                    'creado_por',
                    'modificado_por',
                    'fecha_creacion',
                    'fecha_actualizacion',
                ),
            },
        ),
    )