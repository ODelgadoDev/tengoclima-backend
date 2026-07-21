from django.utils import timezone
from rest_framework import serializers

from core.serializers import AuditoriaSerializerMixin
from cotizaciones.models import Cotizacion

from .models import Pago


class PagoSerializer(serializers.ModelSerializer):
    cotizacion = serializers.PrimaryKeyRelatedField(
        queryset=Cotizacion.objects.filter(activo=True),
    )
    cotizacion_codigo = serializers.CharField(
        source="cotizacion.codigo",
        read_only=True,
    )
    cliente_nombre = serializers.CharField(
        source="cotizacion.cliente.nombre_solicitante",
        read_only=True,
    )
    cliente_empresa = serializers.CharField(
        source="cotizacion.cliente.empresa",
        read_only=True,
    )

    class Meta:
        model = Pago
        fields = [
            "id",
            "cotizacion",
            "cotizacion_codigo",
            "cliente_nombre",
            "cliente_empresa",
            "monto",
            "metodo_pago",
            "referencia",
            "notas",
            "fecha_pago",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "cotizacion_codigo",
            "cliente_nombre",
            "cliente_empresa",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El monto del pago debe ser mayor a 0.",
            )

        return value

    def validate_fecha_pago(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                "La fecha de pago no puede ser futura.",
            )

        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)

        cotizacion = attrs.get(
            "cotizacion",
            getattr(self.instance, "cotizacion", None),
        )
        monto = attrs.get(
            "monto",
            getattr(self.instance, "monto", None),
        )

        errors = {}

        if (
            self.instance
            and "cotizacion" in attrs
            and cotizacion.pk != self.instance.cotizacion_id
        ):
            errors["cotizacion"] = (
                "La cotización de un pago no puede cambiarse."
            )

        if cotizacion and cotizacion.total <= 0:
            errors["cotizacion"] = (
                "No se puede registrar un pago en una cotización "
                "sin total."
            )

        if cotizacion and monto:
            disponible = cotizacion.saldo_pendiente

            if (
                self.instance
                and not self.instance.eliminado
                and self.instance.cotizacion_id == cotizacion.pk
            ):
                disponible += self.instance.monto

            if monto > disponible:
                errors["monto"] = (
                    "El pago no puede ser mayor al saldo disponible "
                    "de la cotización."
                )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class PagoDetalleSerializer(
    AuditoriaSerializerMixin,
    PagoSerializer,
):
    class Meta(PagoSerializer.Meta):
        fields = PagoSerializer.Meta.fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]
        read_only_fields = (
            PagoSerializer.Meta.read_only_fields
            + [
                "activo",
                "eliminado",
                "creado_por",
                "creado_por_username",
                "modificado_por",
                "modificado_por_username",
            ]
        )
