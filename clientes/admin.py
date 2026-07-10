from django.contrib import admin

from .models import ClientePotencial
from core.admin import AuditableAdmin


@admin.register(ClientePotencial)
class ClientePotencialAdmin(AuditableAdmin):
    list_display = (
        'nombre_solicitante',
        'empresa',
        'telefono',
        'estado',
    )

    list_filter = (
        'estado',
    )

    search_fields = (
        'nombre_solicitante',
        'empresa',
        'telefono',
        'direccion',
        'descripcion',
    )

    ordering = (
        '-fecha_creacion',
    )

    fieldsets = (
        (
            'Información del cliente',
            {
                'fields': (
                    'nombre_solicitante',
                    'empresa',
                    'telefono',
                    'direccion',
                    'descripcion',
                    'estado',
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