from rest_framework import serializers


class AuditoriaSerializerMixin(serializers.ModelSerializer):
    creado_por_username = serializers.SerializerMethodField()
    modificado_por_username = serializers.SerializerMethodField()

    def get_creado_por_username(self, obj):
        if obj.creado_por:
            return obj.creado_por.get_full_name() or obj.creado_por.username
        return None

    def get_modificado_por_username(self, obj):
        if obj.modificado_por:
            return obj.modificado_por.get_full_name() or obj.modificado_por.username
        return None