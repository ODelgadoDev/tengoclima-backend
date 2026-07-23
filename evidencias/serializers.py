import mimetypes
from pathlib import Path

from rest_framework import serializers
from rest_framework.reverse import reverse

from core.serializers import AuditoriaSerializerMixin

from .models import (
    EXTENSIONES_PERMITIDAS,
    TAMANIO_MAXIMO_BYTES,
    Evidencia,
)


class EvidenciaSerializer(AuditoriaSerializerMixin):
    cotizacion_codigo = serializers.CharField(
        source="cotizacion.codigo",
        read_only=True,
        allow_null=True,
    )
    proyecto_nombre = serializers.CharField(
        source="proyecto.nombre",
        read_only=True,
        allow_null=True,
    )
    tipo_display = serializers.CharField(
        source="get_tipo_display",
        read_only=True,
    )
    imagen = serializers.FileField(
        source="archivo",
        read_only=True,
    )
    es_imagen = serializers.BooleanField(read_only=True)
    es_pdf = serializers.BooleanField(read_only=True)
    es_cad = serializers.BooleanField(read_only=True)
    clase_archivo = serializers.CharField(read_only=True)
    origen_tipo = serializers.SerializerMethodField()
    origen_id = serializers.SerializerMethodField()
    origen_nombre = serializers.SerializerMethodField()
    url_visualizacion = serializers.SerializerMethodField()
    url_descarga = serializers.SerializerMethodField()

    class Meta:
        model = Evidencia
        fields = [
            "id",
            "cotizacion",
            "cotizacion_codigo",
            "proyecto",
            "proyecto_nombre",
            "tipo",
            "tipo_display",
            "archivo",
            "imagen",
            "nombre_original",
            "extension",
            "mime_type",
            "tamanio_bytes",
            "descripcion",
            "es_imagen",
            "es_pdf",
            "es_cad",
            "clase_archivo",
            "origen_tipo",
            "origen_id",
            "origen_nombre",
            "url_visualizacion",
            "url_descarga",
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "nombre_original",
            "extension",
            "mime_type",
            "tamanio_bytes",
            "activo",
            "eliminado",
            "creado_por",
            "creado_por_username",
            "modificado_por",
            "modificado_por_username",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        extra_kwargs = {
            "archivo": {"required": False},
            "cotizacion": {"required": False, "allow_null": True},
            "proyecto": {"required": False, "allow_null": True},
        }

    def to_internal_value(self, data):
        """Acepta temporalmente `imagen` para no romper clientes anteriores."""
        if data is not None and "archivo" not in data and "imagen" in data:
            data = data.copy()
            data["archivo"] = data.get("imagen")
        return super().to_internal_value(data)

    def validate_archivo(self, archivo):
        extension = Path(archivo.name).suffix.lower().lstrip(".")

        if extension not in EXTENSIONES_PERMITIDAS:
            raise serializers.ValidationError(
                "Formato no permitido. Usa JPG, JPEG, PNG, WEBP, PDF, "
                "DWG, DXF o DWT.",
            )

        if archivo.size <= 0:
            raise serializers.ValidationError("El archivo está vacío.")

        if archivo.size > TAMANIO_MAXIMO_BYTES:
            raise serializers.ValidationError(
                "El archivo no puede superar 50 MB.",
            )

        return archivo

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance

        cotizacion = attrs.get(
            "cotizacion",
            getattr(instance, "cotizacion", None),
        )
        proyecto = attrs.get(
            "proyecto",
            getattr(instance, "proyecto", None),
        )

        if bool(cotizacion) == bool(proyecto):
            raise serializers.ValidationError(
                {
                    "origen": (
                        "Selecciona una cotización o un proyecto, pero no "
                        "ambos."
                    ),
                },
            )

        if instance is None and not attrs.get("archivo"):
            raise serializers.ValidationError(
                {"archivo": "Selecciona el archivo que deseas subir."},
            )

        if instance is not None:
            if (
                "cotizacion" in attrs
                and attrs["cotizacion"] != instance.cotizacion
            ):
                raise serializers.ValidationError(
                    {
                        "cotizacion": (
                            "No se puede cambiar el origen de un archivo. "
                            "Elimínalo y vuelve a subirlo."
                        ),
                    },
                )
            if "proyecto" in attrs and attrs["proyecto"] != instance.proyecto:
                raise serializers.ValidationError(
                    {
                        "proyecto": (
                            "No se puede cambiar el origen de un archivo. "
                            "Elimínalo y vuelve a subirlo."
                        ),
                    },
                )

        return attrs

    def _metadatos_archivo(self, archivo):
        return {
            "nombre_original": Path(archivo.name).name[:255],
            "extension": Path(archivo.name).suffix.lower().lstrip(".")[:10],
            "mime_type": (
                getattr(archivo, "content_type", "")
                or mimetypes.guess_type(archivo.name)[0]
                or ""
            )[:150],
            "tamanio_bytes": max(int(archivo.size or 0), 0),
        }

    def create(self, validated_data):
        archivo = validated_data.get("archivo")
        validated_data.update(self._metadatos_archivo(archivo))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        archivo_anterior = instance.archivo.name if instance.archivo else ""
        archivo_nuevo = validated_data.get("archivo")

        if archivo_nuevo:
            validated_data.update(self._metadatos_archivo(archivo_nuevo))

        actualizado = super().update(instance, validated_data)

        if (
            archivo_nuevo
            and archivo_anterior
            and archivo_anterior != actualizado.archivo.name
        ):
            actualizado.archivo.storage.delete(archivo_anterior)

        return actualizado

    def get_origen_tipo(self, obj):
        if obj.cotizacion_id:
            return "COTIZACION"
        if obj.proyecto_id:
            return "PROYECTO"
        return None

    def get_origen_id(self, obj):
        return obj.cotizacion_id or obj.proyecto_id

    def get_origen_nombre(self, obj):
        return obj.origen_descripcion

    def get_url_visualizacion(self, obj):
        if not obj.archivo:
            return None
        request = self.context.get("request")
        url = obj.archivo.url
        return request.build_absolute_uri(url) if request else url

    def get_url_descarga(self, obj):
        request = self.context.get("request")
        return reverse(
            "evidencias-descargar",
            kwargs={"pk": obj.pk},
            request=request,
        )
