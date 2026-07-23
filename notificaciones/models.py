from django.conf import settings
from django.db import models
from django.db.models import Q


class Notificacion(models.Model):
    TIPO_PROYECTO_ASIGNADO = "PROYECTO_ASIGNADO"
    TIPO_COTIZACION_AUTORIZADA = "COTIZACION_AUTORIZADA"
    TIPO_COTIZACION_CANCELADA = "COTIZACION_CANCELADA"
    TIPO_FACTURA_CREADA = "FACTURA_CREADA"
    TIPO_FACTURA_PAGADA = "FACTURA_PAGADA"
    TIPO_PAGO_REGISTRADO = "PAGO_REGISTRADO"
    TIPO_PROYECTO_PROXIMO = "PROYECTO_PROXIMO"
    TIPO_PROYECTO_ATRASADO = "PROYECTO_ATRASADO"
    TIPO_ARCHIVO_NUEVO = "ARCHIVO_NUEVO"
    TIPO_USUARIO_CREADO = "USUARIO_CREADO"
    TIPO_USUARIO_ACTIVADO = "USUARIO_ACTIVADO"
    TIPO_USUARIO_DESACTIVADO = "USUARIO_DESACTIVADO"
    TIPO_SISTEMA = "SISTEMA"

    TIPOS = [
        (TIPO_PROYECTO_ASIGNADO, "Proyecto asignado"),
        (TIPO_COTIZACION_AUTORIZADA, "Cotización autorizada"),
        (TIPO_COTIZACION_CANCELADA, "Cotización cancelada"),
        (TIPO_FACTURA_CREADA, "Factura cargada"),
        (TIPO_FACTURA_PAGADA, "Factura pagada"),
        (TIPO_PAGO_REGISTRADO, "Pago registrado"),
        (TIPO_PROYECTO_PROXIMO, "Proyecto próximo a vencer"),
        (TIPO_PROYECTO_ATRASADO, "Proyecto atrasado"),
        (TIPO_ARCHIVO_NUEVO, "Archivo nuevo"),
        (TIPO_USUARIO_CREADO, "Usuario creado"),
        (TIPO_USUARIO_ACTIVADO, "Usuario activado"),
        (TIPO_USUARIO_DESACTIVADO, "Usuario desactivado"),
        (TIPO_SISTEMA, "Sistema"),
    ]

    NIVEL_INFO = "INFO"
    NIVEL_EXITO = "EXITO"
    NIVEL_ADVERTENCIA = "ADVERTENCIA"
    NIVEL_ERROR = "ERROR"

    NIVELES = [
        (NIVEL_INFO, "Información"),
        (NIVEL_EXITO, "Éxito"),
        (NIVEL_ADVERTENCIA, "Advertencia"),
        (NIVEL_ERROR, "Error"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="notificaciones_generadas",
        null=True,
        blank=True,
    )
    tipo = models.CharField(max_length=40, choices=TIPOS)
    nivel = models.CharField(
        max_length=20,
        choices=NIVELES,
        default=NIVEL_INFO,
    )
    titulo = models.CharField(max_length=180)
    mensaje = models.TextField()
    ruta = models.CharField(max_length=255, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    objeto_id = models.CharField(max_length=64, blank=True)
    clave = models.CharField(max_length=255, blank=True)
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_creacion", "-id"]
        indexes = [
            models.Index(
                fields=["usuario", "leida", "-fecha_creacion"],
                name="notif_user_read_date",
            ),
            models.Index(
                fields=["tipo", "-fecha_creacion"],
                name="notif_type_date",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "clave"],
                condition=~Q(clave=""),
                name="notif_user_key_unique",
            ),
        ]
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"

    def __str__(self):
        estado = "leída" if self.leida else "pendiente"
        return f"{self.usuario.username}: {self.titulo} ({estado})"
