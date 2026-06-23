from rest_framework import serializers
from .models import Pago


class PagoSerializer(serializers.ModelSerializer):
    cotizacion_codigo = serializers.CharField(
        source='cotizacion.codigo',
        read_only=True
    )

    class Meta:
        model = Pago
        fields = [
            'id',
            'cotizacion',
            'cotizacion_codigo',
            'monto',
            'metodo_pago',
            'referencia',
            'notas',
            'fecha_pago',
            'fecha_creacion',
        ]