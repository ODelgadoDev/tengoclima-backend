import shutil
import tempfile
import zipfile
from pathlib import Path

from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from core.viewsets import BaseModelViewSet
from cotizaciones.models import Cotizacion
from proyectos.models import Proyecto
from usuarios.permissions import EsLecturaOAdministrador

from .models import Evidencia
from .serializers import EvidenciaSerializer


class EvidenciaViewSet(BaseModelViewSet):
    queryset = (
        Evidencia.objects
        .select_related(
            "cotizacion",
            "cotizacion__cliente",
            "cotizacion__proyecto",
            "proyecto",
            "proyecto__cliente",
            "creado_por",
            "modificado_por",
        )
        .order_by("-fecha_creacion")
    )
    serializer_class = EvidenciaSerializer
    permission_classes = [EsLecturaOAdministrador]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    search_fields = [
        "descripcion",
        "nombre_original",
        "extension",
        "cotizacion__codigo",
        "cotizacion__cliente__nombre_solicitante",
        "cotizacion__cliente__empresa",
        "proyecto__nombre",
        "proyecto__cliente__nombre_solicitante",
        "proyecto__cliente__empresa",
    ]
    filterset_fields = [
        "cotizacion",
        "proyecto",
        "tipo",
        "extension",
        "activo",
        "eliminado",
    ]
    ordering_fields = [
        "nombre_original",
        "tamanio_bytes",
        "fecha_creacion",
        "fecha_actualizacion",
    ]

    @action(detail=False, methods=["get"], url_path="eliminados")
    def eliminados(self, request):
        queryset = (
            self.get_queryset()
            .filter(eliminado=True)
            .order_by("-fecha_actualizacion")
        )
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="descargar")
    def descargar(self, request, pk=None):
        instance = self.get_object()

        if not instance.archivo:
            return Response(
                {"detail": "El registro no tiene un archivo disponible."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            archivo = instance.archivo.open("rb")
        except (FileNotFoundError, OSError):
            return Response(
                {"detail": "El archivo físico no se encontró."},
                status=status.HTTP_404_NOT_FOUND,
            )

        nombre = (
            instance.nombre_original
            or Path(instance.archivo.name).name
            or f"archivo-{instance.pk}"
        )
        return FileResponse(
            archivo,
            as_attachment=True,
            filename=nombre,
            content_type=instance.mime_type or "application/octet-stream",
        )

    def _queryset_zip(self, request):
        cotizacion_id = request.query_params.get("cotizacion")
        proyecto_id = request.query_params.get("proyecto")
        tipo = request.query_params.get("tipo")
        incluir_cotizaciones = (
            request.query_params.get("incluir_cotizaciones", "true").lower()
            in {"1", "true", "si", "sí", "yes"}
        )

        if bool(cotizacion_id) == bool(proyecto_id):
            return None, None, Response(
                {
                    "detail": (
                        "Indica exactamente una cotización o un proyecto."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(activo=True, eliminado=False)
        contexto = {}

        if cotizacion_id:
            cotizacion = get_object_or_404(
                Cotizacion.objects.select_related("cliente"),
                pk=cotizacion_id,
            )
            queryset = queryset.filter(cotizacion=cotizacion)
            contexto = {
                "origen": "cotizacion",
                "objeto": cotizacion,
                "nombre": cotizacion.codigo,
            }
        else:
            proyecto = get_object_or_404(
                Proyecto.objects.select_related("cliente"),
                pk=proyecto_id,
            )
            condicion = Q(proyecto=proyecto)
            if incluir_cotizaciones:
                condicion |= Q(cotizacion__proyecto=proyecto)
            queryset = queryset.filter(condicion)
            contexto = {
                "origen": "proyecto",
                "objeto": proyecto,
                "nombre": proyecto.nombre,
            }

        if tipo:
            tipos_validos = {choice[0] for choice in Evidencia.TIPOS}
            if tipo not in tipos_validos:
                return None, None, Response(
                    {
                        "detail": (
                            "Tipo inválido. Usa REFERENCIA, EVIDENCIA o "
                            "TECNICO."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(tipo=tipo)

        return queryset.order_by("tipo", "fecha_creacion", "id"), contexto, None

    def _nombre_zip_interno(self, archivo, contexto):
        carpetas_tipo = {
            Evidencia.TIPO_REFERENCIA: "referencias",
            Evidencia.TIPO_EVIDENCIA: "evidencias",
            Evidencia.TIPO_TECNICO: "tecnicos",
        }
        carpeta_tipo = carpetas_tipo.get(archivo.tipo, "otros")
        nombre = archivo.nombre_original or Path(archivo.archivo.name).name
        nombre = Path(nombre).name
        nombre_unico = f"{archivo.pk:06d}_{nombre}"

        if contexto["origen"] == "proyecto":
            if archivo.proyecto_id:
                return f"proyecto/{carpeta_tipo}/{nombre_unico}"
            codigo = slugify(archivo.cotizacion.codigo) or str(
                archivo.cotizacion_id,
            )
            return (
                f"cotizaciones/{codigo}/{carpeta_tipo}/{nombre_unico}"
            )

        codigo = slugify(archivo.cotizacion.codigo) or str(
            archivo.cotizacion_id,
        )
        return f"{codigo}/{carpeta_tipo}/{nombre_unico}"

    @action(detail=False, methods=["get"], url_path="descargar-zip")
    def descargar_zip(self, request):
        queryset, contexto, error = self._queryset_zip(request)
        if error is not None:
            return error

        archivos = list(queryset)
        if not archivos:
            return Response(
                {"detail": "No hay archivos disponibles para descargar."},
                status=status.HTTP_404_NOT_FOUND,
            )

        temporal = tempfile.TemporaryFile()
        incluidos = 0

        with zipfile.ZipFile(
            temporal,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as comprimido:
            for archivo in archivos:
                if not archivo.archivo:
                    continue

                try:
                    origen = archivo.archivo.open("rb")
                except (FileNotFoundError, OSError):
                    continue

                ruta_zip = self._nombre_zip_interno(archivo, contexto)
                with origen:
                    with comprimido.open(ruta_zip, "w") as destino:
                        shutil.copyfileobj(
                            origen,
                            destino,
                            length=1024 * 1024,
                        )
                incluidos += 1

        if incluidos == 0:
            temporal.close()
            return Response(
                {
                    "detail": (
                        "Los registros existen, pero sus archivos físicos "
                        "no están disponibles."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        temporal.seek(0)
        nombre_base = slugify(contexto["nombre"]) or contexto["origen"]
        respuesta = FileResponse(
            temporal,
            as_attachment=True,
            filename=f"archivos-{nombre_base}.zip",
            content_type="application/zip",
        )
        respuesta["X-Total-Archivos"] = str(incluidos)
        return respuesta
