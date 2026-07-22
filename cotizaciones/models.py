from decimal import Decimal

from django.db import models

from clientes.models import ClientePotencial
from core.models import AuditableModel


class UnidadConceptoMixin:
    UNIDAD_PZA = "PZA"
    UNIDAD_ML = "ML"
    UNIDAD_M2 = "M2"
    UNIDAD_SERV = "SERV"
    UNIDAD_PAQ = "PAQ"
    UNIDAD_LOTE = "LOTE"

    UNIDADES = [
        (UNIDAD_PZA, "Pieza"),
        (UNIDAD_ML, "Metro lineal"),
        (UNIDAD_M2, "Metro cuadrado"),
        (UNIDAD_SERV, "Servicio"),
        (UNIDAD_PAQ, "Paquete"),
        (UNIDAD_LOTE, "Lote"),
    ]


class Cotizacion(AuditableModel):
    ESTADO_PENDIENTE = "PENDIENTE"
    ESTADO_AUTORIZADA = "AUTORIZADA"
    ESTADO_CANCELADA = "CANCELADA"
    # Estado transitorio mientras se migra a proyectos con varias cotizaciones.
    ESTADO_CONVERTIDA = "CONVERTIDA"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_AUTORIZADA, "Autorizada"),
        (ESTADO_CANCELADA, "Cancelada"),
        (ESTADO_CONVERTIDA, "Vinculada a proyecto"),
    ]

    TIPO_LOCAL = "LOCAL"
    TIPO_EXTERIOR = "EXTERIOR"

    TIPOS = [
        (TIPO_LOCAL, "Local"),
        (TIPO_EXTERIOR, "Exterior"),
    ]

    cliente = models.ForeignKey(
        ClientePotencial,
        on_delete=models.CASCADE,
        related_name="cotizaciones",
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
        default=ESTADO_PENDIENTE,
    )

    class Meta:
        ordering = ["-fecha_creacion"]

    def recalcular_totales(self):
        subtotal = sum(
            (concepto.total for concepto in self.conceptos.all()),
            Decimal("0.00"),
        )
        self.subtotal = subtotal
        self.iva = subtotal * Decimal("0.16")
        self.total = self.subtotal + self.iva
        self.save(update_fields=["subtotal", "iva", "total", "fecha_actualizacion"])

    @property
    def total_pagado(self):
        return sum(
            (pago.monto for pago in self.pagos.all()),
            Decimal("0.00"),
        )

    @property
    def saldo_pendiente(self):
        saldo = self.total - self.total_pagado
        return max(saldo, Decimal("0.00"))

    @property
    def estado_cobranza(self):
        if self.total_pagado <= 0:
            return "PENDIENTE"
        if self.total_pagado < self.total:
            return "PARCIAL"
        return "PAGADO"

    def __str__(self):
        return f"{self.codigo} - {self.cliente.nombre_solicitante}"


class ConceptoCatalogo(UnidadConceptoMixin, AuditableModel):
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(max_length=10, choices=UnidadConceptoMixin.UNIDADES)
    precio_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    class Meta:
        verbose_name = "concepto de catálogo"
        verbose_name_plural = "catálogo de conceptos"
        ordering = ["descripcion", "unidad"]

    def __str__(self):
        return f"{self.descripcion} - {self.unidad}"


class ConceptoCotizacion(UnidadConceptoMixin, models.Model):
    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name="conceptos",
    )
    catalogo = models.ForeignKey(
        ConceptoCatalogo,
        on_delete=models.SET_NULL,
        related_name="usos",
        null=True,
        blank=True,
    )
    descripcion = models.CharField(max_length=255)
    unidad = models.CharField(
        max_length=10,
        choices=UnidadConceptoMixin.UNIDADES,
        default=UnidadConceptoMixin.UNIDAD_PZA,
    )
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
