from django.contrib.auth.models import User
from rest_framework import serializers

from clientes.models import ClientePotencial
from core.serializers import AuditoriaSerializerMixin
from cotizaciones.models import Cotizacion

from .models import Proyecto


class CotizacionProyectoResumenSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(
        source="cliente.nombre_solicitante",
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

    class Meta:
        model = Cotizacion
        fields = [
            "id",
            "codigo",
            "cliente",
            "cliente_nombre",
            "descripcion",
            "tipo",
            "estado",
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
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = fields


class ProyectoSerializer(serializers.ModelSerializer):
    cliente = serializers.PrimaryKeyRelatedField(
        queryset=ClientePotencial.objects.filter(activo=True),
    )
    responsable = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            is_active=True,
            perfilusuario__activo=True,
        ),
        allow_null=True,
        required=False,
    )
    cotizaciones_ids = serializers.PrimaryKeyRelatedField(
        queryset=(
            Cotizacion.objects
            .select_related("cliente", "proyecto")
            .filter(activo=True)
        ),
        many=True,
        write_only=True,
        required=False,
    )
    cotizaciones = CotizacionProyectoResumenSerializer(
        many=True,
        read_only=True,
    )

    cliente_nombre = serializers.CharField(
        source="cliente.nombre_solicitante",
        read_only=True,
    )
    cliente_empresa = serializers.CharField(
        source="cliente.empresa",
        read_only=True,
    )
    cliente_telefono = serializers.CharField(
        source="cliente.telefono",
        read_only=True,
    )
    cliente_direccion = serializers.CharField(
        source="cliente.direccion",
        read_only=True,
    )
    responsable_username = serializers.CharField(
        source="responsable.username",
        read_only=True,
        allow_null=True,
    )
    responsable_nombre = serializers.SerializerMethodField()
    cotizaciones_count = serializers.SerializerMethodField()
    total_cotizaciones = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )
    total_pagado = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )
    saldo_pendiente = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )
    estado_cobranza = serializers.CharField(read_only=True)
    total_facturado = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )
    saldo_por_facturar = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        read_only=True,
    )
    estado_facturacion = serializers.CharField(read_only=True)

    class Meta:
        model = Proyecto
        fields = [
            "id",
            "cliente",
            "cliente_nombre",
            "cliente_empresa",
            "cliente_telefono",
            "cliente_direccion",
            "nombre",
            "responsable",
            "responsable_username",
            "responsable_nombre",
            "fecha_inicio",
            "fecha_fin_estimada",
            "fecha_fin_real",
            "estado",
            "notas",
            "cotizaciones_ids",
            "cotizaciones",
            "cotizaciones_count",
            "total_cotizaciones",
            "total_pagado",
            "saldo_pendiente",
            "estado_cobranza",
            "total_facturado",
            "saldo_por_facturar",
            "estado_facturacion",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "cliente_nombre",
            "cliente_empresa",
            "cliente_telefono",
            "cliente_direccion",
            "responsable_username",
            "responsable_nombre",
            "cotizaciones",
            "cotizaciones_count",
            "total_cotizaciones",
            "total_pagado",
            "saldo_pendiente",
            "estado_cobranza",
            "total_facturado",
            "saldo_por_facturar",
            "estado_facturacion",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def get_responsable_nombre(self, obj):
        if not obj.responsable:
            return None
        return obj.responsable.get_full_name().strip() or obj.responsable.username

    def get_cotizaciones_count(self, obj):
        return len(obj.cotizaciones.all())

    def validate_nombre(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "El nombre del proyecto es obligatorio.",
            )
        return value

    def _validar_cotizaciones(self, cotizaciones, cliente):
        ids = [cotizacion.pk for cotizacion in cotizaciones]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                {"cotizaciones_ids": "No repitas una cotización."},
            )

        errores = []
        for cotizacion in cotizaciones:
            if cotizacion.cliente_id != cliente.pk:
                errores.append(
                    f"{cotizacion.codigo}: pertenece a otro cliente.",
                )
            elif cotizacion.estado != Cotizacion.ESTADO_AUTORIZADA:
                errores.append(
                    f"{cotizacion.codigo}: debe estar autorizada.",
                )
            elif cotizacion.proyecto_id is not None:
                errores.append(
                    f"{cotizacion.codigo}: ya pertenece a un proyecto.",
                )

        if errores:
            raise serializers.ValidationError(
                {"cotizaciones_ids": errores},
            )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        cliente = attrs.get(
            "cliente",
            getattr(self.instance, "cliente", None),
        )
        cotizaciones = attrs.get("cotizaciones_ids", [])

        if cliente is None:
            raise serializers.ValidationError(
                {"cliente": "Selecciona el cliente del proyecto."},
            )

        if not cliente.activo or cliente.eliminado:
            raise serializers.ValidationError(
                {"cliente": "El cliente seleccionado no está activo."},
            )

        if self.instance is not None and "cotizaciones_ids" in attrs:
            raise serializers.ValidationError(
                {
                    "cotizaciones_ids": (
                        "Para agregar o retirar cotizaciones utiliza las "
                        "acciones del proyecto."
                    ),
                },
            )

        if (
            self.instance is not None
            and cliente.pk != self.instance.cliente_id
            and self.instance.cotizaciones.exists()
        ):
            raise serializers.ValidationError(
                {
                    "cliente": (
                        "No puedes cambiar el cliente mientras el proyecto "
                        "tenga cotizaciones vinculadas."
                    ),
                },
            )

        if cotizaciones:
            self._validar_cotizaciones(cotizaciones, cliente)

        fecha_inicio = attrs.get(
            "fecha_inicio",
            getattr(self.instance, "fecha_inicio", None),
        )
        fecha_fin_estimada = attrs.get(
            "fecha_fin_estimada",
            getattr(self.instance, "fecha_fin_estimada", None),
        )
        fecha_fin_real = attrs.get(
            "fecha_fin_real",
            getattr(self.instance, "fecha_fin_real", None),
        )

        errors = {}
        if (
            fecha_inicio
            and fecha_fin_estimada
            and fecha_fin_estimada < fecha_inicio
        ):
            errors["fecha_fin_estimada"] = (
                "La fecha estimada de finalización no puede ser anterior "
                "a la fecha de inicio."
            )
        if fecha_inicio and fecha_fin_real and fecha_fin_real < fecha_inicio:
            errors["fecha_fin_real"] = (
                "La fecha real de finalización no puede ser anterior "
                "a la fecha de inicio."
            )
        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        self.cotizaciones_para_vincular = validated_data.pop(
            "cotizaciones_ids",
            [],
        )
        return super().create(validated_data)


class ProyectoDetalleSerializer(
    AuditoriaSerializerMixin,
    ProyectoSerializer,
):
    class Meta(ProyectoSerializer.Meta):
        fields = ProyectoSerializer.Meta.fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]
        read_only_fields = ProyectoSerializer.Meta.read_only_fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]


class VincularCotizacionSerializer(serializers.Serializer):
    cotizacion = serializers.PrimaryKeyRelatedField(
        queryset=(
            Cotizacion.objects
            .select_related("cliente", "proyecto")
            .filter(activo=True)
        ),
    )
