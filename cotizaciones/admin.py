from django.contrib import admin

from core.admin import AuditableAdmin

from .models import ConceptoCatalogo, ConceptoCotizacion, Cotizacion


class ConceptoCotizacionInline(admin.TabularInline):
    model = ConceptoCotizacion
    extra = 0
    fields = (
        "catalogo",
        "descripcion",
        "unidad",
        "cantidad",
        "precio_unitario",
        "total",
    )
    readonly_fields = ("total",)


@admin.register(Cotizacion)
class CotizacionAdmin(AuditableAdmin):
    list_display = (
        "codigo",
        "cliente",
        "tipo",
        "estado",
        "subtotal",
        "iva",
        "total",
    )
    list_filter = ("estado", "tipo", "activo", "eliminado")
    search_fields = (
        "codigo",
        "descripcion",
        "cliente__nombre_solicitante",
        "cliente__empresa",
    )
    readonly_fields = ("subtotal", "iva", "total")
    inlines = [ConceptoCotizacionInline]


@admin.register(ConceptoCatalogo)
class ConceptoCatalogoAdmin(AuditableAdmin):
    list_display = (
        "descripcion",
        "unidad",
        "precio_unitario",
        "activo",
        "fecha_actualizacion",
    )
    list_filter = ("unidad", "activo", "eliminado")
    search_fields = ("descripcion",)
    ordering = ("descripcion", "unidad")


@admin.register(ConceptoCotizacion)
class ConceptoCotizacionAdmin(admin.ModelAdmin):
    list_display = (
        "cotizacion",
        "descripcion",
        "unidad",
        "cantidad",
        "precio_unitario",
        "total",
    )
    list_filter = ("unidad",)
    search_fields = ("descripcion", "cotizacion__codigo", "catalogo__descripcion")
