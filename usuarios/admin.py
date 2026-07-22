from django.contrib import admin

from .models import PerfilUsuario, RegistroActividad


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "rol",
        "telefono",
        "activo",
        "requiere_cambio_contrasena",
        "fecha_creacion",
    )
    list_filter = (
        "rol",
        "activo",
        "requiere_cambio_contrasena",
    )
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__email",
        "telefono",
    )
    readonly_fields = (
        "fecha_creacion",
        "fecha_actualizacion",
    )


@admin.register(RegistroActividad)
class RegistroActividadAdmin(admin.ModelAdmin):
    list_display = (
        "fecha",
        "usuario",
        "accion",
        "modelo_etiqueta",
        "objeto_repr",
    )
    list_filter = (
        "accion",
        "modelo",
        "fecha",
    )
    search_fields = (
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "descripcion",
        "objeto_repr",
    )
    readonly_fields = (
        "usuario",
        "accion",
        "modelo",
        "modelo_etiqueta",
        "objeto_id",
        "objeto_repr",
        "descripcion",
        "cambios",
        "ruta",
        "ip",
        "user_agent",
        "fecha",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
