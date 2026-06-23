from rest_framework import serializers
from .models import CategoriaGasto, Gasto


class CategoriaGastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaGasto
        fields = '__all__'


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