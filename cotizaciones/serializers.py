from rest_framework import serializers
from .models import Cotizacion, ConceptoCotizacion


class ConceptoCotizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConceptoCotizacion
        fields = [
            'id',
            'descripcion',
            'unidad',
            'cantidad',
            'precio_unitario',
            'total',
        ]

    def validate_descripcion(self, value):
        if not value.strip():
            raise serializers.ValidationError('La descripción del concepto es obligatoria.')
        return value

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError('La cantidad debe ser mayor a 0.')
        return value

    def validate_precio_unitario(self, value):
        if value < 0:
            raise serializers.ValidationError('El precio unitario no puede ser negativo.')
        return value


class CotizacionSerializer(serializers.ModelSerializer):
    conceptos = ConceptoCotizacionSerializer(many=True, read_only=True)

    cliente_nombre = serializers.CharField(
        source='cliente.nombre_solicitante',
        read_only=True
    )

    cliente_empresa = serializers.CharField(
        source='cliente.empresa',
        read_only=True
    )

    total_pagado = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    saldo_pendiente = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    estado_cobranza = serializers.CharField(read_only=True)

    class Meta:
        model = Cotizacion
        fields = [
            'id',
            'codigo',
            'cliente',
            'cliente_nombre',
            'cliente_empresa',
            'descripcion',
            'tipo',
            'estimado_tiempo',
            'subtotal',
            'iva',
            'total',
            'total_pagado',
            'saldo_pendiente',
            'estado_cobranza',
            'estado',
            'fecha_creacion',
            'fecha_actualizacion',
            'conceptos',
        ]

    def validate_codigo(self, value):
        if not value.strip():
            raise serializers.ValidationError('El código de la cotización es obligatorio.')
        return value.upper()

    def validate_descripcion(self, value):
        if not value.strip():
            raise serializers.ValidationError('La descripción de la cotización es obligatoria.')
        return value