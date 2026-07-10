from django.contrib import admin

from .models import Proyecto
from core.admin import AuditableAdmin


@admin.register(Proyecto)
class ProyectoAdmin(AuditableAdmin):
    list_display = (
        'nombre',
        'cotizacion',
        'responsable',
        'estado',
        'fecha_inicio',
        'fecha_fin_estimada',
        'fecha_fin_real',
    )

    list_filter = (
        'estado',
        'fecha_inicio',
        'fecha_fin_estimada',
    )

    search_fields = (
        'nombre',
        'cotizacion__codigo',
        'cotizacion__cliente__nombre_solicitante',
        'cotizacion__cliente__empresa',
        'responsable__username',
        'responsable__first_name',
        'responsable__last_name',
    )

    ordering = (
        '-fecha_creacion',
    )

    fieldsets = (
        (
            'Información del proyecto',
            {
                'fields': (
                    'cotizacion',
                    'nombre',
                    'responsable',
                    'estado',
                    'notas',
                )
            },
        ),
        (
            'Fechas',
            {
                'fields': (
                    'fecha_inicio',
                    'fecha_fin_estimada',
                    'fecha_fin_real',
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