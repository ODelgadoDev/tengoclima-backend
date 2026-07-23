from pathlib import Path

from django.utils import timezone
from rest_framework import serializers

from core.serializers import AuditoriaSerializerMixin
from cotizaciones.models import Cotizacion

from .models import FacturaDocumento, Pago


MAX_FACTURA_BYTES = 25 * 1024 * 1024


def validar_pdf(value):
    extension = Path(value.name or "").suffix.lower()
    if extension != ".pdf":
        raise serializers.ValidationError(
            "La factura debe cargarse en formato PDF.",
        )

    if value.size > MAX_FACTURA_BYTES:
        raise serializers.ValidationError(
            "El PDF no puede superar 25 MB.",
        )

    posicion = value.tell() if hasattr(value, "tell") else 0
    encabezado = value.read(5)
    if hasattr(value, "seek"):
        value.seek(posicion)

    if encabezado != b"%PDF-":
        raise serializers.ValidationError(
            "El archivo seleccionado no parece ser un PDF válido.",
        )

    return value


class FacturaDocumentoSerializer(serializers.ModelSerializer):
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
    proyecto = serializers.IntegerField(
        source="cotizacion.proyecto_id",
        read_only=True,
        allow_null=True,
    )
    proyecto_nombre = serializers.CharField(
        source="cotizacion.proyecto.nombre",
        read_only=True,
        allow_null=True,
    )
    monto_pagado = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    saldo_pendiente = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    pagos_count = serializers.SerializerMethodField()

    class Meta:
        model = FacturaDocumento
        fields = [
            "id",
            "cotizacion",
            "cotizacion_codigo",
            "cliente_nombre",
            "cliente_empresa",
            "proyecto",
            "proyecto_nombre",
            "folio",
            "archivo_pdf",
            "importe",
            "fecha_emision",
            "estado",
            "fecha_pago",
            "observaciones",
            "monto_pagado",
            "saldo_pendiente",
            "pagos_count",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "cotizacion_codigo",
            "cliente_nombre",
            "cliente_empresa",
            "proyecto",
            "proyecto_nombre",
            "estado",
            "fecha_pago",
            "monto_pagado",
            "saldo_pendiente",
            "pagos_count",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def get_pagos_count(self, obj):
        return obj.pagos.count()

    def validate_folio(self, value):
        value = value.strip().upper()
        if not value:
            raise serializers.ValidationError(
                "El folio de la factura es obligatorio.",
            )
        return value

    def validate_archivo_pdf(self, value):
        return validar_pdf(value)

    def validate_importe(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "El importe de la factura debe ser mayor a 0.",
            )
        return value

    def validate_fecha_emision(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                "La fecha de emisión no puede ser futura.",
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        cotizacion = attrs.get(
            "cotizacion",
            getattr(self.instance, "cotizacion", None),
        )
        importe = attrs.get(
            "importe",
            getattr(self.instance, "importe", None),
        )

        errors = {}

        if self.instance is not None:
            if (
                "cotizacion" in attrs
                and cotizacion.pk != self.instance.cotizacion_id
            ):
                errors["cotizacion"] = (
                    "La cotización de una factura no puede cambiarse."
                )

            protegidos = {
                "cotizacion",
                "folio",
                "archivo_pdf",
                "importe",
                "fecha_emision",
            }
            enviados = protegidos.intersection(self.initial_data.keys())
            if (
                self.instance.estado != FacturaDocumento.ESTADO_PENDIENTE
                and enviados
            ):
                errors["factura"] = (
                    "Una factura pagada o cancelada no puede modificar sus "
                    "datos principales. Reábrela o corrige primero sus pagos."
                )

        if cotizacion is None:
            errors["cotizacion"] = "Selecciona una cotización."
        elif cotizacion.eliminado or not cotizacion.activo:
            errors["cotizacion"] = "La cotización seleccionada no está activa."
        elif cotizacion.estado != Cotizacion.ESTADO_AUTORIZADA:
            errors["cotizacion"] = (
                "Solo se pueden cargar facturas a cotizaciones autorizadas."
            )
        elif cotizacion.total <= 0:
            errors["cotizacion"] = (
                "No se puede facturar una cotización sin total."
            )

        if (
            self.instance is not None
            and importe is not None
            and importe < self.instance.monto_pagado
        ):
            errors["importe"] = (
                "El importe no puede ser menor a los pagos ya vinculados "
                "a la factura."
            )

        if cotizacion is not None and importe is not None:
            facturas = FacturaDocumento.objects.filter(
                cotizacion=cotizacion,
            ).exclude(estado=FacturaDocumento.ESTADO_CANCELADA)
            if self.instance is not None:
                facturas = facturas.exclude(pk=self.instance.pk)

            total_otros = sum(
                (factura.importe for factura in facturas),
                0,
            )
            if total_otros + importe > cotizacion.total:
                errors["importe"] = (
                    "La suma de facturas activas no puede superar el total "
                    "de la cotización."
                )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class FacturaDocumentoDetalleSerializer(
    AuditoriaSerializerMixin,
    FacturaDocumentoSerializer,
):
    class Meta(FacturaDocumentoSerializer.Meta):
        fields = FacturaDocumentoSerializer.Meta.fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]
        read_only_fields = FacturaDocumentoSerializer.Meta.read_only_fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]


class PagoSerializer(serializers.ModelSerializer):
    cotizacion = serializers.PrimaryKeyRelatedField(
        queryset=Cotizacion.objects.filter(activo=True),
        required=False,
    )
    factura = serializers.PrimaryKeyRelatedField(
        queryset=FacturaDocumento.objects.filter(activo=True),
        required=False,
        allow_null=True,
    )
    factura_folio = serializers.CharField(
        source="factura.folio",
        read_only=True,
        allow_null=True,
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
            "factura",
            "factura_folio",
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
            "factura_folio",
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
        factura = attrs.get(
            "factura",
            getattr(self.instance, "factura", None),
        )
        cotizacion = attrs.get(
            "cotizacion",
            getattr(self.instance, "cotizacion", None),
        )
        monto = attrs.get(
            "monto",
            getattr(self.instance, "monto", None),
        )

        if factura is not None and cotizacion is None:
            cotizacion = factura.cotizacion
            attrs["cotizacion"] = cotizacion

        errors = {}

        if cotizacion is None:
            errors["cotizacion"] = (
                "Selecciona una cotización o una factura."
            )
        elif cotizacion.eliminado or not cotizacion.activo:
            errors["cotizacion"] = "La cotización seleccionada no está activa."
        elif cotizacion.estado == Cotizacion.ESTADO_CANCELADA:
            errors["cotizacion"] = (
                "No se pueden registrar pagos en una cotización cancelada."
            )

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
                "No se puede registrar un pago en una cotización sin total."
            )

        if factura is not None:
            if factura.eliminado or not factura.activo:
                errors["factura"] = "La factura seleccionada no está activa."
            elif factura.estado == FacturaDocumento.ESTADO_CANCELADA:
                errors["factura"] = (
                    "No se pueden registrar pagos en una factura cancelada."
                )
            elif cotizacion and factura.cotizacion_id != cotizacion.pk:
                errors["factura"] = (
                    "La factura no pertenece a la cotización seleccionada."
                )
            elif (
                factura.estado == FacturaDocumento.ESTADO_PAGADA
                and not (
                    self.instance
                    and self.instance.factura_id == factura.pk
                )
            ):
                errors["factura"] = "La factura ya está pagada."

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

        if factura is not None and monto:
            disponible_factura = factura.saldo_pendiente
            if (
                self.instance
                and not self.instance.eliminado
                and self.instance.factura_id == factura.pk
            ):
                disponible_factura += self.instance.monto

            if monto > disponible_factura:
                errors["monto"] = (
                    "El pago no puede ser mayor al saldo pendiente "
                    "de la factura."
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
        read_only_fields = PagoSerializer.Meta.read_only_fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]


class FacturaMarcarPagadaSerializer(serializers.Serializer):
    fecha_pago = serializers.DateField()
    metodo_pago = serializers.ChoiceField(
        choices=Pago.METODO_PAGO_CHOICES,
    )
    referencia = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=100,
    )
    notas = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    pago_existente = serializers.PrimaryKeyRelatedField(
        queryset=Pago.objects.filter(activo=True),
        required=False,
        allow_null=True,
    )

    def validate_fecha_pago(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                "La fecha de pago no puede ser futura.",
            )
        return value


class FacturaCancelarSerializer(serializers.Serializer):
    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
    )
