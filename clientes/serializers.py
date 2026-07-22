from rest_framework import serializers

from core.serializers import AuditoriaSerializerMixin

from .models import ClientePotencial


class ClientePotencialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientePotencial
        fields = [
            "id",
            "nombre_solicitante",
            "empresa",
            "telefono",
            "direccion",
            "descripcion",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "fecha_creacion",
            "fecha_actualizacion",
        ]

    def validate_nombre_solicitante(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError(
                "El nombre del solicitante es obligatorio.",
            )
        return value

    def validate_telefono(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El teléfono es obligatorio.")
        return value


class ClientePotencialDetalleSerializer(
    AuditoriaSerializerMixin,
    ClientePotencialSerializer,
):
    class Meta(ClientePotencialSerializer.Meta):
        fields = ClientePotencialSerializer.Meta.fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]
        read_only_fields = ClientePotencialSerializer.Meta.read_only_fields + [
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
        ]
