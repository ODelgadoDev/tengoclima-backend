from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from core.pagination import PaginacionEstandar
from core.viewsets import ActivityLoggingMixin, BaseModelViewSet
from usuarios.permissions import EsLecturaOAdministrador, EsUsuarioActivo

from .models import CategoriaGasto, Gasto
from .reportes import construir_csv, construir_excel
from .serializers import (
    CategoriaGastoSerializer,
    GastoDetalleSerializer,
    GastoSerializer,
)
from .services import obtener_movimientos, parsear_filtros, resumir_movimientos


class CategoriaGastoViewSet(
    ActivityLoggingMixin,
    viewsets.ModelViewSet,
):
    queryset = CategoriaGasto.objects.all().order_by("nombre")
    serializer_class = CategoriaGastoSerializer
    permission_classes = [EsLecturaOAdministrador]

    search_fields = ["nombre", "descripcion"]
    filterset_fields = ["activo"]
    ordering_fields = ["nombre", "activo"]


class GastoViewSet(BaseModelViewSet):
    queryset = (
        Gasto.objects.select_related(
            "categoria",
            "proyecto__cliente",
            "cotizacion__cliente",
            "cotizacion__proyecto",
        )
        .order_by("-fecha_gasto")
    )
    serializer_class = GastoSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return GastoDetalleSerializer
        return GastoSerializer

    search_fields = [
        "concepto",
        "proveedor",
        "notas",
        "categoria__nombre",
        "proyecto__nombre",
        "cotizacion__codigo",
        "cotizacion__cliente__nombre_solicitante",
        "cotizacion__cliente__empresa",
    ]
    filterset_fields = [
        "categoria",
        "proyecto",
        "cotizacion",
        "metodo_pago",
        "fecha_gasto",
    ]
    ordering_fields = [
        "concepto",
        "proveedor",
        "monto",
        "iva",
        "metodo_pago",
        "fecha_gasto",
        "fecha_creacion",
    ]


class LibroContableView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        filtros = parsear_filtros(request.query_params)
        movimientos = obtener_movimientos(filtros)
        resumen = resumir_movimientos(movimientos)

        paginator = PaginacionEstandar()
        page = paginator.paginate_queryset(movimientos, request, view=self)
        response = paginator.get_paginated_response(page)
        response.data["resumen"] = resumen
        return response


class LibroResumenView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        filtros = parsear_filtros(request.query_params)
        movimientos = obtener_movimientos(filtros)
        return Response(resumir_movimientos(movimientos))


class LibroExportarExcelView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        filtros = parsear_filtros(request.query_params)
        movimientos = obtener_movimientos(filtros)
        archivo = construir_excel(movimientos, filtros)
        filename = timezone.localtime().strftime(
            "libro-contable-%Y%m%d-%H%M.xlsx",
        )
        response = HttpResponse(
            archivo.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class LibroExportarCsvView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        filtros = parsear_filtros(request.query_params)
        movimientos = obtener_movimientos(filtros)
        contenido = construir_csv(movimientos)
        filename = timezone.localtime().strftime(
            "libro-contable-%Y%m%d-%H%M.csv",
        )
        response = HttpResponse(
            contenido,
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
