from django.contrib import admin
from .models import CategoriaGasto, Gasto


@admin.register(CategoriaGasto)
class CategoriaGastoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    search_fields = ('nombre',)


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = (
        'concepto',
        'categoria',
        'proveedor',
        'monto',
        'metodo_pago',
        'fecha_gasto',
    )
    list_filter = ('categoria', 'metodo_pago', 'fecha_gasto')
    search_fields = ('concepto', 'proveedor')