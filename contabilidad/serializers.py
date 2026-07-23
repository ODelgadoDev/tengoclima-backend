from django.utils import timezone
from rest_framework import serializers

from core.serializers import AuditoriaSerializerMixin
from cotizaciones.models import Cotizacion
from proyectos.models import Proyecto

from .models import CategoriaGasto, Gasto


class CategoriaGastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaGasto
        fields = "__all__"

    def validate_nombre(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "El nombre de la categoría es obligatorio.",
            )
        return value


class GastoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(
        source="categoria.nombre",
        read_only=True,
    )
    proyecto_nombre = serializers.CharField(
        source="proyecto.nombre",
        read_only=True,
        allow_null=True,
    )
    cotizacion_codigo = serializers.CharField(
        source="cotizacion.codigo",
        read_only=True,
        allow_null=True,
    )
    cliente_id = serializers.SerializerMethodField()
    cliente_nombre = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Gasto
        fields = [
            "id",
            "categoria",
            "categoria_nombre",
            "proyecto",
            "proyecto_nombre",
            "cotizacion",
            "cotizacion_codigo",
            "cliente_id",
            "cliente_nombre",
            "concepto",
            "proveedor",
            "monto",
            "subtotal",
            "iva",
            "metodo_pago",
            "comprobante",
            "notas",
            "fecha_gasto",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def get_cliente_id(self, obj):
        cliente = obj.cliente
        return cliente.id if cliente else None

    def get_cliente_nombre(self, obj):
        cliente = obj.cliente
        if cliente is None:
            return None
        return cliente.empresa or cliente.nombre_solicitante

    def validate_concepto(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "El concepto del gasto es obligatorio.",
            )
        return value

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El monto del gasto debe ser mayor a 0.",
            )
        return value

    def validate_iva(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El IVA no puede ser negativo.",
            )
        return value

    def validate_fecha_gasto(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                "La fecha del gasto no puede ser futura.",
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        monto = attrs.get("monto", getattr(self.instance, "monto", None))
        iva = attrs.get("iva", getattr(self.instance, "iva", 0))
        proyecto = attrs.get(
            "proyecto",
            getattr(self.instance, "proyecto", None),
        )
        cotizacion = attrs.get(
            "cotizacion",
            getattr(self.instance, "cotizacion", None),
        )

        errors = {}

        if monto is not None and iva is not None and iva > monto:
            errors["iva"] = "El IVA no puede ser mayor al monto total."

        if cotizacion is not None:
            if cotizacion.eliminado or not cotizacion.activo:
                errors["cotizacion"] = (
                    "La cotización seleccionada no está activa."
                )
            if proyecto is not None:
                if cotizacion.proyecto_id != proyecto.id:
                    errors["cotizacion"] = (
                        "La cotización no pertenece al proyecto seleccionado."
                    )

        if proyecto is not None and (proyecto.eliminado or not proyecto.activo):
            errors["proyecto"] = "El proyecto seleccionado no está activo."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class GastoDetalleSerializer(AuditoriaSerializerMixin, GastoSerializer):
    class Meta(GastoSerializer.Meta):
        fields = GastoSerializer.Meta.fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]
        read_only_fields = [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
