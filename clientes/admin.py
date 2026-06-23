from django.contrib import admin
from .models import ClientePotencial


@admin.register(ClientePotencial)
class ClientePotencialAdmin(admin.ModelAdmin):
    list_display = ('nombre_solicitante', 'empresa', 'telefono', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('nombre_solicitante', 'empresa', 'telefono')