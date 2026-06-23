from django.contrib import admin
from .models import Proyecto


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'cotizacion',
        'responsable',
        'estado',
        'fecha_inicio',
        'fecha_fin_estimada',
        'fecha_fin_real',
    )

    list_filter = ('estado', 'fecha_inicio', 'fecha_fin_estimada')

    search_fields = (
        'nombre',
        'cotizacion__codigo',
        'cotizacion__cliente__nombre_solicitante',
        'cotizacion__cliente__empresa',
    )