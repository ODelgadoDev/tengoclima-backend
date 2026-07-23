from decimal import Decimal

from rest_framework import serializers

from core.serializers import AuditoriaSerializerMixin

from .models import ConceptoCatalogo, ConceptoCotizacion, Cotizacion


class ConceptoCatalogoSerializer(serializers.ModelSerializer):
    usos = serializers.IntegerField(source="cantidad_usos", read_only=True)

    class Meta:
        model = ConceptoCatalogo
        fields = [
            "id",
            "descripcion",
            "unidad",
            "precio_unitario",
            "usos",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "usos",
            "activo",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def validate_descripcion(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "La descripción del concepto es obligatoria.",
            )
        return value

    def validate_precio_unitario(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El precio unitario no puede ser negativo.",
            )
        return value


class ConceptoCotizacionSerializer(serializers.ModelSerializer):
    catalogo = serializers.PrimaryKeyRelatedField(
        queryset=ConceptoCatalogo.objects.filter(activo=True),
        required=False,
        allow_null=True,
    )
    catalogo_descripcion = serializers.CharField(
        source="catalogo.descripcion",
        read_only=True,
        allow_null=True,
    )
    descripcion = serializers.CharField(required=False)
    unidad = serializers.ChoiceField(
        choices=ConceptoCotizacion.UNIDADES,
        required=False,
    )
    precio_unitario = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
    )
    cotizacion_codigo = serializers.CharField(
        source="cotizacion.codigo",
        read_only=True,
    )

    class Meta:
        model = ConceptoCotizacion
        fields = [
            "id",
            "cotizacion",
            "cotizacion_codigo",
            "catalogo",
            "catalogo_descripcion",
            "descripcion",
            "unidad",
            "cantidad",
            "precio_unitario",
            "total",
        ]
        read_only_fields = [
            "id",
            "cotizacion_codigo",
            "catalogo_descripcion",
            "total",
        ]

    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "La cantidad debe ser mayor a 0.",
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        catalogo = attrs.get(
            "catalogo",
            getattr(self.instance, "catalogo", None),
        )

        if catalogo is not None and not catalogo.activo:
            raise serializers.ValidationError(
                {"catalogo": "El concepto seleccionado está inactivo."},
            )

        if catalogo is not None:
            attrs.setdefault("descripcion", catalogo.descripcion)
            attrs.setdefault("unidad", catalogo.unidad)
            attrs.setdefault("precio_unitario", catalogo.precio_unitario)

        descripcion = attrs.get(
            "descripcion",
            getattr(self.instance, "descripcion", ""),
        )
        unidad = attrs.get(
            "unidad",
            getattr(self.instance, "unidad", None),
        )
        precio = attrs.get(
            "precio_unitario",
            getattr(self.instance, "precio_unitario", None),
        )

        if not str(descripcion or "").strip():
            raise serializers.ValidationError(
                {"descripcion": "La descripción del concepto es obligatoria."},
            )
        if unidad is None:
            raise serializers.ValidationError(
                {"unidad": "La unidad del concepto es obligatoria."},
            )
        if precio is None:
            raise serializers.ValidationError(
                {"precio_unitario": "El precio unitario es obligatorio."},
            )
        if precio < 0:
            raise serializers.ValidationError(
                {"precio_unitario": "El precio unitario no puede ser negativo."},
            )

        cotizacion = attrs.get(
            "cotizacion",
            getattr(self.instance, "cotizacion", None),
        )
        if (
            self.instance is not None
            and "cotizacion" in attrs
            and cotizacion.pk != self.instance.cotizacion_id
        ):
            raise serializers.ValidationError(
                {
                    "cotizacion": (
                        "La cotización de un concepto no puede cambiarse."
                    ),
                },
            )

        cantidad = attrs.get(
            "cantidad",
            getattr(self.instance, "cantidad", None),
        )
        if cotizacion is not None and cantidad is not None and precio is not None:
            otros = cotizacion.conceptos.all()
            if self.instance is not None:
                otros = otros.exclude(pk=self.instance.pk)
            subtotal_estimado = sum(
                (concepto.total for concepto in otros),
                Decimal("0.00"),
            ) + (cantidad * precio)
            total_estimado = subtotal_estimado * Decimal("1.16")
            comprometido = max(
                cotizacion.total_pagado,
                cotizacion.total_facturado,
            )
            if total_estimado < comprometido:
                raise serializers.ValidationError(
                    {
                        "concepto": (
                            "El cambio reduciría el total de la cotización "
                            "por debajo de lo ya facturado o pagado."
                        ),
                    },
                )

        attrs["descripcion"] = str(descripcion).strip()
        return attrs


class CotizacionSerializer(serializers.ModelSerializer):
    conceptos = ConceptoCotizacionSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(
        source="cliente.nombre_solicitante",
        read_only=True,
    )
    cliente_empresa = serializers.CharField(
        source="cliente.empresa",
        read_only=True,
    )
    total_pagado = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    saldo_pendiente = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    estado_cobranza = serializers.CharField(read_only=True)
    facturas_count = serializers.IntegerField(read_only=True)
    total_facturado = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    saldo_por_facturar = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    estado_facturacion = serializers.CharField(read_only=True)
    proyecto = serializers.PrimaryKeyRelatedField(read_only=True)
    proyecto_nombre = serializers.CharField(
        source="proyecto.nombre",
        read_only=True,
        allow_null=True,
    )
    proyecto_eliminado = serializers.BooleanField(
        source="proyecto.eliminado",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Cotizacion
        fields = [
            "id",
            "codigo",
            "cliente",
            "cliente_nombre",
            "cliente_empresa",
            "proyecto",
            "proyecto_nombre",
            "proyecto_eliminado",
            "descripcion",
            "tipo",
            "estimado_tiempo",
            "subtotal",
            "iva",
            "total",
            "total_pagado",
            "saldo_pendiente",
            "estado_cobranza",
            "facturas_count",
            "total_facturado",
            "saldo_por_facturar",
            "estado_facturacion",
            "estado",
            "fecha_creacion",
            "fecha_actualizacion",
            "conceptos",
        ]
        read_only_fields = [
            "id",
            "cliente_nombre",
            "cliente_empresa",
            "proyecto",
            "proyecto_nombre",
            "proyecto_eliminado",
            "subtotal",
            "iva",
            "total",
            "total_pagado",
            "saldo_pendiente",
            "estado_cobranza",
            "facturas_count",
            "total_facturado",
            "saldo_por_facturar",
            "estado_facturacion",
            "estado",
            "fecha_creacion",
            "fecha_actualizacion",
            "conceptos",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        cliente = attrs.get(
            "cliente",
            getattr(self.instance, "cliente", None),
        )

        if (
            self.instance is not None
            and self.instance.proyecto_id is not None
            and cliente is not None
            and cliente.pk != self.instance.cliente_id
        ):
            raise serializers.ValidationError(
                {
                    "cliente": (
                        "No puedes cambiar el cliente de una cotización "
                        "vinculada a un proyecto."
                    ),
                },
            )

        return attrs

    def validate_codigo(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError(
                "El código de la cotización es obligatorio.",
            )
        return value

    def validate_descripcion(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "La descripción de la cotización es obligatoria.",
            )
        return value


class CotizacionDetalleSerializer(
    AuditoriaSerializerMixin,
    CotizacionSerializer,
):
    class Meta(CotizacionSerializer.Meta):
        fields = CotizacionSerializer.Meta.fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]
        read_only_fields = CotizacionSerializer.Meta.read_only_fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]
