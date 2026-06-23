from django.contrib import admin
from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        'cotizacion',
        'monto',
        'metodo_pago',
        'referencia',
        'fecha_pago',
        'fecha_creacion',
    )
    list_filter = ('metodo_pago', 'fecha_pago')
    search_fields = (
        'cotizacion__codigo',
        'cotizacion__descripcion',
        'referencia',
    )