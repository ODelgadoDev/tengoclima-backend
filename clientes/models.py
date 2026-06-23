from django.db import models


class ClientePotencial(models.Model):
    ESTADO_PENDIENTE = 'PENDIENTE'
    ESTADO_EN_TRAMITE = 'EN_TRAMITE'
    ESTADO_AUTORIZADO = 'AUTORIZADO'
    ESTADO_RECHAZADO = 'RECHAZADO'

    ESTADOS = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_EN_TRAMITE, 'En trámite'),
        (ESTADO_AUTORIZADO, 'Autorizado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
    ]

    nombre_solicitante = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField(blank=True, null=True)
    descripcion = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_PENDIENTE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre_solicitante} - {self.estado}"