from django.contrib import admin

from .models import CategoriaGasto, Gasto
from core.admin import AuditableAdmin


@admin.register(CategoriaGasto)
class CategoriaGastoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'activo',
    )

    list_filter = (
        'activo',
    )

    search_fields = (
        'nombre',
        'descripcion',
    )

    ordering = (
        'nombre',
    )


@admin.register(Gasto)
class GastoAdmin(AuditableAdmin):
    list_display = (
        'concepto',
        'categoria',
        'proveedor',
        'monto',
        'metodo_pago',
        'fecha_gasto',
    )

    list_filter = (
        'categoria',
        'metodo_pago',
        'fecha_gasto',
    )

    search_fields = (
        'concepto',
        'proveedor',
        'categoria__nombre',
        'notas',
    )

    ordering = (
        '-fecha_gasto',
        '-fecha_creacion',
    )

    fieldsets = (
        (
            'Información del gasto',
            {
                'fields': (
                    'categoria',
                    'concepto',
                    'proveedor',
                    'monto',
                    'metodo_pago',
                    'comprobante',
                    'notas',
                    'fecha_gasto',
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