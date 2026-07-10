from django.contrib import admin

from .models import Cotizacion, ConceptoCotizacion
from core.admin import AuditableAdmin


class ConceptoCotizacionInline(admin.TabularInline):
    model = ConceptoCotizacion
    extra = 1
    readonly_fields = ('total',)


@admin.register(Cotizacion)
class CotizacionAdmin(AuditableAdmin):
    list_display = (
        'codigo',
        'cliente',
        'tipo',
        'subtotal',
        'iva',
        'total',
        'estado',
    )

    list_filter = (
        'estado',
        'tipo',
    )

    search_fields = (
        'codigo',
        'descripcion',
        'cliente__nombre_solicitante',
        'cliente__empresa',
    )

    readonly_fields = (
        'subtotal',
        'iva',
        'total',
    )

    fieldsets = (
        (
            'Información de la cotización',
            {
                'fields': (
                    'cliente',
                    'codigo',
                    'descripcion',
                    'tipo',
                    'estimado_tiempo',
                    'estado',
                )
            },
        ),
        (
            'Totales',
            {
                'fields': (
                    'subtotal',
                    'iva',
                    'total',
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

    inlines = [ConceptoCotizacionInline]

    ordering = (
        '-fecha_creacion',
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.recalcular_totales()


@admin.register(ConceptoCotizacion)
class ConceptoCotizacionAdmin(admin.ModelAdmin):
    list_display = (
        'cotizacion',
        'descripcion',
        'unidad',
        'cantidad',
        'precio_unitario',
        'total',
    )

    list_filter = (
        'unidad',
    )

    search_fields = (
        'descripcion',
        'cotizacion__codigo',
    )

    readonly_fields = (
        'total',
    )