from decimal import Decimal

from django.contrib import admin
from .models import Cotizacion, ConceptoCotizacion


class ConceptoCotizacionInline(admin.TabularInline):
    model = ConceptoCotizacion
    extra = 1
    readonly_fields = ('total',)


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'cliente',
        'tipo',
        'subtotal',
        'iva',
        'total',
        'estado',
        'fecha_creacion',
    )

    list_filter = ('estado', 'tipo', 'fecha_creacion')

    search_fields = (
        'codigo',
        'cliente__nombre_solicitante',
        'cliente__empresa',
    )

    fields = (
        'cliente',
        'codigo',
        'descripcion',
        'tipo',
        'estimado_tiempo',
        'estado',
        'subtotal',
        'iva',
        'total',
    )

    readonly_fields = ('subtotal', 'iva', 'total')

    inlines = [ConceptoCotizacionInline]

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

    list_filter = ('unidad',)

    search_fields = (
        'descripcion',
        'cotizacion__codigo',
    )

    readonly_fields = ('total',)