from rest_framework import serializers


class ResultadoBusquedaGlobalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tipo = serializers.ChoiceField(
        choices=[
            "CLIENTE",
            "COTIZACION",
            "PROYECTO",
            "USUARIO",
        ],
    )
    titulo = serializers.CharField()
    subtitulo = serializers.CharField(allow_blank=True)
    descripcion = serializers.CharField(allow_blank=True)
    estado = serializers.CharField(allow_blank=True)
    ruta = serializers.CharField()


class BusquedaGlobalSerializer(serializers.Serializer):
    query = serializers.CharField()
    min_caracteres = serializers.IntegerField()
    total = serializers.IntegerField()
    clientes = ResultadoBusquedaGlobalSerializer(many=True)
    cotizaciones = ResultadoBusquedaGlobalSerializer(many=True)
    proyectos = ResultadoBusquedaGlobalSerializer(many=True)
    usuarios = ResultadoBusquedaGlobalSerializer(many=True)
