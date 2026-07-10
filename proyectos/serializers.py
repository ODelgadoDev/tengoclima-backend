from rest_framework import serializers

from .models import Proyecto
from core.serializers import AuditoriaSerializerMixin


class ProyectoSerializer(serializers.ModelSerializer):
    cotizacion_codigo = serializers.CharField(
        source='cotizacion.codigo',
        read_only=True
    )

    cliente_nombre = serializers.CharField(
        source='cotizacion.cliente.nombre_solicitante',
        read_only=True
    )

    cliente_empresa = serializers.CharField(
        source='cotizacion.cliente.empresa',
        read_only=True
    )

    total_cotizacion = serializers.DecimalField(
        source='cotizacion.total',
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    responsable_nombre = serializers.SerializerMethodField()

    def get_responsable_nombre(self, obj):
        if obj.responsable:
            return obj.responsable.get_full_name() or obj.responsable.username
        return None

    class Meta:
        model = Proyecto
        fields = [
            'id',
            'cotizacion',
            'cotizacion_codigo',
            'cliente_nombre',
            'cliente_empresa',
            'total_cotizacion',
            'nombre',
            'responsable',
            'responsable_nombre',
            'fecha_inicio',
            'fecha_fin_estimada',
            'fecha_fin_real',
            'estado',
            'notas',
            'fecha_creacion',
            'fecha_actualizacion',
        ]


class ProyectoDetalleSerializer(AuditoriaSerializerMixin, ProyectoSerializer):
    class Meta(ProyectoSerializer.Meta):
        fields = ProyectoSerializer.Meta.fields + [
            'activo',
            'eliminado',
            'creado_por',
            'creado_por_username',
            'modificado_por',
            'modificado_por_username',
        ]

        read_only_fields = [
            'activo',
            'eliminado',
            'creado_por',
            'creado_por_username',
            'modificado_por',
            'modificado_por_username',
            'fecha_creacion',
            'fecha_actualizacion',
        ]