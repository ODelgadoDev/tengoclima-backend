from django.contrib import admin

from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "tipo",
        "nivel",
        "titulo",
        "leida",
        "fecha_creacion",
    )
    list_filter = ("tipo", "nivel", "leida", "fecha_creacion")
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "titulo",
        "mensaje",
    )
    readonly_fields = (
        "usuario",
        "actor",
        "tipo",
        "nivel",
        "titulo",
        "mensaje",
        "ruta",
        "modelo",
        "objeto_id",
        "clave",
        "leida",
        "fecha_lectura",
        "fecha_creacion",
    )
    ordering = ("-fecha_creacion",)
