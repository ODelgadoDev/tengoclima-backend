from django.db import models
from django.contrib.auth.models import User

from cotizaciones.models import Cotizacion
from core.models import AuditableModel


class Proyecto(AuditableModel):
    ESTADO_PENDIENTE = 'PENDIENTE'
    ESTADO_EN_PROCESO = 'EN_PROCESO'
    ESTADO_DETENIDO = 'DETENIDO'
    ESTADO_FINALIZADO = 'FINALIZADO'
    ESTADO_FACTURADO = 'FACTURADO'
    ESTADO_PAGADO = 'PAGADO'

    ESTADOS = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_EN_PROCESO, 'En proceso'),
        (ESTADO_DETENIDO, 'Detenido'),
        (ESTADO_FINALIZADO, 'Finalizado'),
        (ESTADO_FACTURADO, 'Facturado'),
        (ESTADO_PAGADO, 'Pagado'),
    ]

    cotizacion = models.OneToOneField(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name='proyecto'
    )

    nombre = models.CharField(max_length=150)

    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin_estimada = models.DateField(blank=True, null=True)
    fecha_fin_real = models.DateField(blank=True, null=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE
    )

    notas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} - {self.estado}"