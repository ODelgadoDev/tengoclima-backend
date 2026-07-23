from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models

from clientes.models import ClientePotencial
from core.models import AuditableModel


class Proyecto(AuditableModel):
    ESTADO_PENDIENTE = "PENDIENTE"
    ESTADO_EN_PROCESO = "EN_PROCESO"
    ESTADO_DETENIDO = "DETENIDO"
    ESTADO_FINALIZADO = "FINALIZADO"
    ESTADO_FACTURADO = "FACTURADO"
    ESTADO_PAGADO = "PAGADO"

    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_EN_PROCESO, "En proceso"),
        (ESTADO_DETENIDO, "Detenido"),
        (ESTADO_FINALIZADO, "Finalizado"),
        (ESTADO_FACTURADO, "Facturado"),
        (ESTADO_PAGADO, "Pagado"),
    ]

    cliente = models.ForeignKey(
        ClientePotencial,
        on_delete=models.PROTECT,
        related_name="proyectos",
    )
    nombre = models.CharField(max_length=150)
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin_estimada = models.DateField(blank=True, null=True)
    fecha_fin_real = models.DateField(blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default=ESTADO_PENDIENTE,
    )
    notas = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha_creacion"]

    @property
    def total_cotizaciones(self):
        return sum(
            (cotizacion.total for cotizacion in self.cotizaciones.all()),
            Decimal("0.00"),
        )

    @property
    def total_facturado(self):
        return sum(
            (cotizacion.total_facturado for cotizacion in self.cotizaciones.all()),
            Decimal("0.00"),
        )

    @property
    def saldo_por_facturar(self):
        return max(
            self.total_cotizaciones - self.total_facturado,
            Decimal("0.00"),
        )

    @property
    def estado_facturacion(self):
        total = self.total_cotizaciones
        facturado = self.total_facturado

        if facturado <= 0:
            return "SIN_FACTURA"
        if total > 0 and facturado < total:
            return "FACTURADA_PARCIAL"
        return "FACTURADA"

    @property
    def total_pagado(self):
        return sum(
            (cotizacion.total_pagado for cotizacion in self.cotizaciones.all()),
            Decimal("0.00"),
        )

    @property
    def saldo_pendiente(self):
        return max(
            self.total_cotizaciones - self.total_pagado,
            Decimal("0.00"),
        )

    @property
    def estado_cobranza(self):
        total = self.total_cotizaciones
        pagado = self.total_pagado

        if pagado <= 0:
            return "PENDIENTE"
        if total > 0 and pagado < total:
            return "PARCIAL"
        return "PAGADO"

    def __str__(self):
        return f"{self.nombre} - {self.estado}"
