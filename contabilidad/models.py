from decimal import Decimal

from django.db import models

from core.models import AuditableModel


class CategoriaGasto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Gasto(AuditableModel):
    METODO_PAGO_CHOICES = [
        ("EFECTIVO", "Efectivo"),
        ("TRANSFERENCIA", "Transferencia"),
        ("TARJETA", "Tarjeta"),
        ("CHEQUE", "Cheque"),
        ("OTRO", "Otro"),
    ]

    categoria = models.ForeignKey(
        CategoriaGasto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gastos",
    )
    proyecto = models.ForeignKey(
        "proyectos.Proyecto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gastos",
    )
    cotizacion = models.ForeignKey(
        "cotizaciones.Cotizacion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gastos",
    )
    concepto = models.CharField(max_length=255)
    proveedor = models.CharField(max_length=150, blank=True, null=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    iva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="IVA incluido dentro del monto total del gasto.",
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_PAGO_CHOICES,
    )
    comprobante = models.FileField(
        upload_to="comprobantes_gastos/",
        blank=True,
        null=True,
    )
    notas = models.TextField(blank=True, null=True)
    fecha_gasto = models.DateField()

    @property
    def subtotal(self):
        return max(self.monto - self.iva, Decimal("0.00"))

    @property
    def cliente(self):
        if self.cotizacion_id:
            return self.cotizacion.cliente
        if self.proyecto_id:
            return self.proyecto.cliente
        return None

    def __str__(self):
        return f"{self.concepto} - ${self.monto}"
