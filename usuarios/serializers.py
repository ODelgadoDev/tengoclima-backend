from rest_framework import serializers
from .models import PerfilUsuario


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', read_only=True)
    first_name = serializers.CharField(source='usuario.first_name', read_only=True)
    last_name = serializers.CharField(source='usuario.last_name', read_only=True)
    email = serializers.EmailField(source='usuario.email', read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = [
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'rol',
            'telefono',
            'activo',
            'fecha_creacion',
        ]