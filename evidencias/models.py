from django.db import models
from cotizaciones.models import Cotizacion


class Evidencia(models.Model):
    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name='evidencias'
    )

    imagen = models.ImageField(upload_to='evidencias/')
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidencia {self.id} - {self.cotizacion.codigo}"