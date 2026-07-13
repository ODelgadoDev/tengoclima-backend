from django.contrib import admin

from .models import Pago
from core.admin import AuditableAdmin


@admin.register(Pago)
class PagoAdmin(AuditableAdmin):
    list_display = (
        'cotizacion',
        'monto',
        'metodo_pago',
        'referencia',
        'fecha_pago',
    )

    list_filter = (
        'metodo_pago',
        'fecha_pago',
    )

    search_fields = (
        'cotizacion__codigo',
        'cotizacion__descripcion',
        'cotizacion__cliente__nombre_solicitante',
        'cotizacion__cliente__empresa',
        'referencia',
        'notas',
    )

    ordering = (
        '-fecha_pago',
        '-fecha_creacion',
    )

    fieldsets = (
        (
            'Información del pago',
            {
                'fields': (
                    'cotizacion',
                    'monto',
                    'metodo_pago',
                    'referencia',
                    'notas',
                    'fecha_pago',
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