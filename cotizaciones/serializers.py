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

    estado_cobranza = serializers.CharField(
        read_only=True
    )

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