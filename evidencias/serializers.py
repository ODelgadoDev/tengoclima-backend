from rest_framework import serializers

from .models import Evidencia
from core.serializers import AuditoriaSerializerMixin


class EvidenciaSerializer(AuditoriaSerializerMixin):
    cotizacion_codigo = serializers.CharField(
        source='cotizacion.codigo',
        read_only=True
    )

    class Meta:
        model = Evidencia
        fields = [
            'id',
            'cotizacion',
            'cotizacion_codigo',
            'imagen',
            'descripcion',

            'activo',
            'eliminado',
            'creado_por',
            'creado_por_username',
            'modificado_por',
            'modificado_por_username',
            'fecha_creacion',
            'fecha_actualizacion',
        ]

        read_only_fields = [
            'activo',
            'eliminado',
            'creado_por',
            'creado_por_username',
            'modificado_por',
            'modificado_por_username',
            'fecha_creacion',
            'fecha_actualizacion',
        ]