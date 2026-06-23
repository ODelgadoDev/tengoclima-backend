from django.contrib import admin
from .models import Evidencia


@admin.register(Evidencia)
class EvidenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cotizacion', 'descripcion', 'fecha_subida')
    search_fields = ('cotizacion__codigo', 'descripcion')
    list_filter = ('fecha_subida',)