from django.db import models

from cotizaciones.models import Cotizacion
from core.models import AuditableModel


class Pago(AuditableModel):
    METODO_PAGO_CHOICES = [
        ('EFECTIVO', 'Efectivo'),
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
        ('CHEQUE', 'Cheque'),
        ('OTRO', 'Otro'),
    ]

    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name='pagos'
    )

    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    referencia = models.CharField(max_length=100, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    fecha_pago = models.DateField()

    def __str__(self):
        return f'Pago ${self.monto} - {self.cotizacion.codigo}'