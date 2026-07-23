from rest_framework import serializers

from .models import Notificacion


class NotificacionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(
        source="get_tipo_display",
        read_only=True,
    )
    nivel_display = serializers.CharField(
        source="get_nivel_display",
        read_only=True,
    )
    actor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            "id",
            "tipo",
            "tipo_display",
            "nivel",
            "nivel_display",
            "titulo",
            "mensaje",
            "ruta",
            "modelo",
            "objeto_id",
            "leida",
            "fecha_lectura",
            "fecha_creacion",
            "actor_nombre",
        ]
        read_only_fields = fields

    def get_actor_nombre(self, obj):
        actor = obj.actor
        if actor is None:
            return "Sistema"

        nombre = actor.get_full_name().strip()
        return nombre or actor.username
