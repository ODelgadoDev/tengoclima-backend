from django.contrib.auth.models import User
from rest_framework import serializers

from core.serializers import AuditoriaSerializerMixin
from cotizaciones.models import Cotizacion

from .models import Proyecto


class ProyectoSerializer(serializers.ModelSerializer):
    cotizacion = serializers.PrimaryKeyRelatedField(
        queryset=Cotizacion.objects.select_related("cliente"),
    )
    responsable = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(
            is_active=True,
            perfilusuario__activo=True,
        ),
        allow_null=True,
        required=False,
    )

    cotizacion_codigo = serializers.CharField(
        source="cotizacion.codigo",
        read_only=True,
    )
    cotizacion_estado = serializers.CharField(
        source="cotizacion.estado",
        read_only=True,
    )
    cotizacion_descripcion = serializers.CharField(
        source="cotizacion.descripcion",
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
    cliente_telefono = serializers.CharField(
        source="cotizacion.cliente.telefono",
        read_only=True,
    )
    cliente_direccion = serializers.CharField(
        source="cotizacion.cliente.direccion",
        read_only=True,
    )
    total_cotizacion = serializers.DecimalField(
        source="cotizacion.total",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    responsable_username = serializers.CharField(
        source="responsable.username",
        read_only=True,
        allow_null=True,
    )
    responsable_nombre = serializers.SerializerMethodField()

    def get_responsable_nombre(self, obj):
        if not obj.responsable:
            return None

        return (
            obj.responsable.get_full_name().strip()
            or obj.responsable.username
        )

    class Meta:
        model = Proyecto
        fields = [
            "id",
            "cotizacion",
            "cotizacion_codigo",
            "cotizacion_estado",
            "cotizacion_descripcion",
            "cliente_nombre",
            "cliente_empresa",
            "cliente_telefono",
            "cliente_direccion",
            "total_cotizacion",
            "nombre",
            "responsable",
            "responsable_username",
            "responsable_nombre",
            "fecha_inicio",
            "fecha_fin_estimada",
            "fecha_fin_real",
            "estado",
            "notas",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "cotizacion_codigo",
            "cotizacion_estado",
            "cotizacion_descripcion",
            "cliente_nombre",
            "cliente_empresa",
            "cliente_telefono",
            "cliente_direccion",
            "total_cotizacion",
            "responsable_username",
            "responsable_nombre",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def validate_nombre(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "El nombre del proyecto es obligatorio.",
            )

        return value

    def validate_cotizacion(self, cotizacion):
        if self.instance:
            if cotizacion.pk != self.instance.cotizacion_id:
                raise serializers.ValidationError(
                    "La cotización de un proyecto no puede cambiarse.",
                )

            return cotizacion

        proyecto_existente = (
            Proyecto.all_objects
            .filter(cotizacion_id=cotizacion.pk)
            .first()
        )

        if proyecto_existente:
            if proyecto_existente.eliminado:
                raise serializers.ValidationError(
                    "Esta cotización ya pertenece a un proyecto "
                    "eliminado. Restaura ese proyecto desde la papelera.",
                )

            raise serializers.ValidationError(
                "Esta cotización ya fue convertida en proyecto.",
            )

        if not cotizacion.activo or cotizacion.eliminado:
            raise serializers.ValidationError(
                "La cotización seleccionada no está activa.",
            )

        if cotizacion.estado != Cotizacion.ESTADO_AUTORIZADA:
            raise serializers.ValidationError(
                "Solo una cotización autorizada puede convertirse "
                "en proyecto.",
            )

        return cotizacion

    def validate(self, attrs):
        attrs = super().validate(attrs)

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
                "La fecha estimada de finalización no puede ser "
                "anterior a la fecha de inicio."
            )

        if (
            fecha_inicio
            and fecha_fin_real
            and fecha_fin_real < fecha_inicio
        ):
            errors["fecha_fin_real"] = (
                "La fecha real de finalización no puede ser "
                "anterior a la fecha de inicio."
            )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


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
        read_only_fields = (
            ProyectoSerializer.Meta.read_only_fields
            + [
                "activo",
                "eliminado",
                "creado_por",
                "creado_por_username",
                "modificado_por",
                "modificado_por_username",
            ]
        )
