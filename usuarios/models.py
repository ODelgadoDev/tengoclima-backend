from django.conf import settings
from django.db import models


def ruta_foto_perfil(instance, filename):
    """Organiza las fotografías por usuario."""
    return f"perfiles/{instance.usuario_id}/{filename}"


class PerfilUsuario(models.Model):
    ROL_DUENO = "DUENO"
    ROL_ADMINISTRADOR = "ADMINISTRADOR"
    ROL_AYUDANTE = "AYUDANTE"

    ROLES = [
        (ROL_DUENO, "Dueño"),
        (ROL_ADMINISTRADOR, "Administrador"),
        (ROL_AYUDANTE, "Ayudante"),
    ]

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default=ROL_AYUDANTE,
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(
        upload_to=ruta_foto_perfil,
        blank=True,
        null=True,
    )
    activo = models.BooleanField(default=True)
    requiere_cambio_contrasena = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.rol}"


class RegistroActividad(models.Model):
    ACCION_CREAR = "CREAR"
    ACCION_EDITAR = "EDITAR"
    ACCION_ELIMINAR = "ELIMINAR"
    ACCION_RESTAURAR = "RESTAURAR"
    ACCION_ELIMINAR_DEFINITIVO = "ELIMINAR_DEFINITIVO"
    ACCION_ACTIVAR = "ACTIVAR"
    ACCION_DESACTIVAR = "DESACTIVAR"
    ACCION_CAMBIAR_CONTRASENA = "CAMBIAR_CONTRASENA"
    ACCION_RESTABLECER_CONTRASENA = "RESTABLECER_CONTRASENA"

    ACCIONES = [
        (ACCION_CREAR, "Creó"),
        (ACCION_EDITAR, "Editó"),
        (ACCION_ELIMINAR, "Envió a papelera"),
        (ACCION_RESTAURAR, "Restauró"),
        (ACCION_ELIMINAR_DEFINITIVO, "Eliminó definitivamente"),
        (ACCION_ACTIVAR, "Activó"),
        (ACCION_DESACTIVAR, "Desactivó"),
        (ACCION_CAMBIAR_CONTRASENA, "Cambió su contraseña"),
        (ACCION_RESTABLECER_CONTRASENA, "Restableció una contraseña"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actividades",
    )
    accion = models.CharField(max_length=30, choices=ACCIONES)
    modelo = models.CharField(max_length=100)
    modelo_etiqueta = models.CharField(max_length=100)
    objeto_id = models.CharField(max_length=64, blank=True)
    objeto_repr = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    cambios = models.JSONField(default=dict, blank=True)
    ruta = models.CharField(max_length=255, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        indexes = [
            models.Index(
                fields=["usuario", "-fecha"],
                name="actividad_usuario_fecha",
            ),
            models.Index(
                fields=["modelo", "objeto_id"],
                name="actividad_objeto",
            ),
        ]
        verbose_name = "registro de actividad"
        verbose_name_plural = "registros de actividad"

    def __str__(self):
        usuario = self.usuario.username if self.usuario else "Sistema"
        return f"{usuario} - {self.get_accion_display()} - {self.objeto_repr}"
