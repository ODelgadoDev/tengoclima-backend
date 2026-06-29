from django.utils import timezone
from rest_framework import serializers
from .models import CategoriaGasto, Gasto


class CategoriaGastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaGasto
        fields = '__all__'

    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError('El nombre de la categoría es obligatorio.')
        return value


class GastoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(
        source='categoria.nombre',
        read_only=True
    )

    class Meta:
        model = Gasto
        fields = [
            'id',
            'categoria',
            'categoria_nombre',
            'concepto',
            'proveedor',
            'monto',
            'metodo_pago',
            'comprobante',
            'notas',
            'fecha_gasto',
            'fecha_creacion',
        ]

    def validate_concepto(self, value):
        if not value.strip():
            raise serializers.ValidationError('El concepto del gasto es obligatorio.')
        return value

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError('El monto del gasto debe ser mayor a 0.')
        return value

    def validate_fecha_gasto(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError('La fecha del gasto no puede ser futura.')
        return value