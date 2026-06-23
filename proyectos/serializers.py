from rest_framework import serializers
from .models import Proyecto


class ProyectoSerializer(serializers.ModelSerializer):
    cotizacion_codigo = serializers.CharField(
        source='cotizacion.codigo',
        read_only=True
    )

    cliente_nombre = serializers.CharField(
        source='cotizacion.cliente.nombre_solicitante',
        read_only=True
    )

    cliente_empresa = serializers.CharField(
        source='cotizacion.cliente.empresa',
        read_only=True
    )

    total_cotizacion = serializers.DecimalField(
        source='cotizacion.total',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Proyecto
        fields = [
            'id',
            'cotizacion',
            'cotizacion_codigo',
            'cliente_nombre',
            'cliente_empresa',
            'total_cotizacion',
            'nombre',
            'responsable',
            'fecha_inicio',
            'fecha_fin_estimada',
            'fecha_fin_real',
            'estado',
            'notas',
            'fecha_creacion',
            'fecha_actualizacion',
        ]