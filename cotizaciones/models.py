from decimal import Decimal

from django.db import models
from clientes.models import ClientePotencial
from core.models import AuditableModel


class Cotizacion(AuditableModel):
    ESTADO_PENDIENTE = 'PENDIENTE'
    ESTADO_AUTORIZADA = 'AUTORIZADA'
    ESTADO_RECHAZADA = 'RECHAZADA'
    ESTADO_CONVERTIDA = 'CONVERTIDA'

    ESTADOS = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_AUTORIZADA, 'Autorizada'),
        (ESTADO_RECHAZADA, 'Rechazada'),
        (ESTADO_CONVERTIDA, 'Convertida a proyecto'),
    ]

    TIPO_LOCAL = 'LOCAL'
    TIPO_EXTERIOR = 'EXTERIOR'

    TIPOS = [
        (TIPO_LOCAL, 'Local'),
        (TIPO_EXTERIOR, 'Exterior'),
    ]

    cliente = models.ForeignKey(
        ClientePotencial,
        on_delete=models.CASCADE,
        related_name='cotizaciones'
    )
    codigo = models.CharField(max_length=30, unique=True)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS, default=TIPO_LOCAL)
    estimado_tiempo = models.CharField(max_length=100, blank=True, null=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE
    )

    def recalcular_totales(self):
        subtotal = sum(concepto.total for concepto in self.conceptos.all())

        self.subtotal = subtotal
        self.iva = subtotal * Decimal('0.16')
        self.total = self.subtotal + self.iva

        self.save(update_fields=['subtotal', 'iva', 'total', 'fecha_actualizacion'])

    @property
    def total_pagado(self):
        return sum(pago.monto for pago in self.pagos.all())

    @property
    def saldo_pendiente(self):
        saldo = self.total - self.total_pagado

        if saldo < 0:
            return Decimal('0.00')

        return saldo

    @property
    def estado_cobranza(self):
        if self.total_pagado <= 0:
            return 'PENDIENTE'

        if self.total_pagado < self.total:
            return 'PARCIAL'

        return 'PAGADO'

    def __str__(self):
        return f"{self.codigo} - {self.cliente.nombre_solicitante}"


class ConceptoCotizacion(models.Model):
    UNIDAD_PZA = 'PZA'
    UNIDAD_ML = 'ML'
    UNIDAD_M2 = 'M2'
    UNIDAD_SERV = 'SERV'
    UNIDAD_PAQ = 'PAQ'

    UNIDADES = [
        (UNIDAD_PZA, 'Pieza'),
        (UNIDAD_ML, 'Metro lineal'),
        (UNIDAD_M2, 'Metro cuadrado'),
        (UNIDAD_SERV, 'Servicio'),
        (UNIDAD_PAQ, 'Paquete'),
    ]

    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name='conceptos'
    )
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=10, choices=UNIDADES, default=UNIDAD_PZA)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        self.cotizacion.recalcular_totales()

    def delete(self, *args, **kwargs):
        cotizacion = self.cotizacion
        super().delete(*args, **kwargs)
        cotizacion.recalcular_totales()

    def __str__(self):
        return f"{self.descripcion} - {self.cantidad} {self.unidad}"