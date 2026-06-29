from django.utils import timezone
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

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto del pago debe ser mayor a 0.')
        return value

    def validate_fecha_pago(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('La fecha de pago no puede ser futura.')
        return value

    def validate(self, data):
        cotizacion = data.get('cotizacion')
        monto = data.get('monto')

        if cotizacion and cotizacion.total <= 0:
            raise serializers.ValidationError(
                'No se puede registrar un pago en una cotización sin total.'
            )

        if cotizacion and monto and monto > cotizacion.saldo_pendiente:
            raise serializers.ValidationError(
                'El pago no puede ser mayor al saldo pendiente de la cotización.'
            )

        return data