from django.contrib import admin

from core.admin import AuditableAdmin

from .models import ClientePotencial


@admin.register(ClientePotencial)
class ClientePotencialAdmin(AuditableAdmin):
    list_display = (
        "nombre_solicitante",
        "empresa",
        "telefono",
        "activo",
        "fecha_creacion",
    )
    list_filter = ("activo", "eliminado")
    search_fields = (
        "nombre_solicitante",
        "empresa",
        "telefono",
        "direccion",
        "descripcion",
    )
    ordering = ("-fecha_creacion",)
    fieldsets = (
        (
            "Información del cliente",
            {
                "fields": (
                    "nombre_solicitante",
                    "empresa",
                    "telefono",
                    "direccion",
                    "descripcion",
                ),
            },
        ),
        (
            "Auditoría",
            {
                "classes": ("collapse",),
                "fields": (
                    "activo",
                    "eliminado",
                    "creado_por",
                    "modificado_por",
                    "fecha_creacion",
                    "fecha_actualizacion",
                ),
            },
        ),
    )
