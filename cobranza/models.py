from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.db import models

from cotizaciones.models import Cotizacion
from core.models import AuditableModel


def factura_upload_to(instance, filename):
    extension = Path(filename).suffix.lower() or ".pdf"
    cotizacion_id = instance.cotizacion_id or "sin-cotizacion"
    return (
        f"facturas/cotizacion_{cotizacion_id}/"
        f"{uuid4().hex}{extension}"
    )


class FacturaDocumento(AuditableModel):
    ESTADO_PENDIENTE = "PENDIENTE"
    ESTADO_PAGADA = "PAGADA"
    ESTADO_CANCELADA = "CANCELADA"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente de pago"),
        (ESTADO_PAGADA, "Pagada"),
        (ESTADO_CANCELADA, "Cancelada"),
    ]

    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.PROTECT,
        related_name="facturas",
    )
    folio = models.CharField(max_length=100, unique=True)
    archivo_pdf = models.FileField(upload_to=factura_upload_to)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_emision = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE,
    )
    fecha_pago = models.DateField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha_emision", "-fecha_creacion"]
        verbose_name = "factura"
        verbose_name_plural = "facturas"

    @property
    def monto_pagado(self):
        return sum(
            (pago.monto for pago in self.pagos.all()),
            Decimal("0.00"),
        )

    @property
    def saldo_pendiente(self):
        return max(
            self.importe - self.monto_pagado,
            Decimal("0.00"),
        )

    def __str__(self):
        return f"Factura {self.folio} - {self.cotizacion.codigo}"


class Pago(AuditableModel):
    METODO_PAGO_CHOICES = [
        ("EFECTIVO", "Efectivo"),
        ("TRANSFERENCIA", "Transferencia"),
        ("TARJETA", "Tarjeta"),
        ("CHEQUE", "Cheque"),
        ("OTRO", "Otro"),
    ]

    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name="pagos",
    )
    factura = models.ForeignKey(
        FacturaDocumento,
        on_delete=models.SET_NULL,
        related_name="pagos",
        null=True,
        blank=True,
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
    )
    referencia = models.CharField(max_length=100, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    fecha_pago = models.DateField()

    def __str__(self):
        return f"Pago ${self.monto} - {self.cotizacion.codigo}"
