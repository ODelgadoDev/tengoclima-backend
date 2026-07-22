from django.db import models

from core.models import AuditableModel


class ClientePotencial(AuditableModel):
    nombre_solicitante = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150, blank=True, null=True)
    telefono = models.CharField(max_length=20)
    direccion = models.TextField(blank=True, null=True)
    descripcion = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        if self.empresa:
            return f"{self.nombre_solicitante} - {self.empresa}"
        return self.nombre_solicitante
