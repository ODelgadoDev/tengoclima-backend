from rest_framework import serializers

from .models import PerfilUsuario


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )
    first_name = serializers.CharField(
        source="usuario.first_name",
        read_only=True,
    )
    last_name = serializers.CharField(
        source="usuario.last_name",
        read_only=True,
    )
    email = serializers.EmailField(
        source="usuario.email",
        read_only=True,
    )

    class Meta:
        model = PerfilUsuario
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "rol",
            "telefono",
            "activo",
            "fecha_creacion",
        ]


class UsuarioResponsableSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para selectores de responsables.

    El id corresponde al User de Django porque Proyecto.responsable
    apunta directamente a AUTH_USER_MODEL, no a PerfilUsuario.
    """

    id = serializers.IntegerField(
        source="usuario.id",
        read_only=True,
    )
    username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )
    first_name = serializers.CharField(
        source="usuario.first_name",
        read_only=True,
    )
    last_name = serializers.CharField(
        source="usuario.last_name",
        read_only=True,
    )
    email = serializers.EmailField(
        source="usuario.email",
        read_only=True,
    )
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = PerfilUsuario
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "nombre_completo",
            "email",
            "rol",
        ]

    def get_nombre_completo(self, obj):
        return (
            obj.usuario.get_full_name().strip()
            or obj.usuario.username
        )
