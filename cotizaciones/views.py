from django.db import transaction
from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import ActivityLoggingMixin, BaseModelViewSet
from usuarios.models import RegistroActividad
from usuarios.permissions import EsLecturaOAdministrador

from .models import ConceptoCatalogo, ConceptoCotizacion, Cotizacion
from .serializers import (
    ConceptoCatalogoSerializer,
    ConceptoCotizacionSerializer,
    CotizacionDetalleSerializer,
    CotizacionSerializer,
)


class CotizacionViewSet(BaseModelViewSet):
    queryset = (
        Cotizacion.objects
        .select_related("cliente")
        .prefetch_related("conceptos", "pagos")
        .order_by("-fecha_creacion")
    )
    serializer_class = CotizacionSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CotizacionDetalleSerializer
        return CotizacionSerializer

    search_fields = [
        "codigo",
        "descripcion",
        "cliente__nombre_solicitante",
        "cliente__empresa",
        "conceptos__descripcion",
    ]
    filterset_fields = ["estado", "tipo", "cliente"]
    ordering_fields = [
        "codigo",
        "subtotal",
        "iva",
        "total",
        "estado",
        "fecha_creacion",
        "fecha_actualizacion",
    ]

    def _cambiar_estado(self, request, instance, nuevo_estado, mensaje):
        estado_anterior = instance.estado
        if estado_anterior == nuevo_estado:
            serializer = self.get_serializer(instance)
            return Response(
                {"success": True, "message": mensaje, "cotizacion": serializer.data},
                status=status.HTTP_200_OK,
            )

        instance.estado = nuevo_estado
        instance.modificado_por = request.user
        instance.save(
            update_fields=["estado", "modificado_por", "fecha_actualizacion"],
        )
        self.registrar_actividad(
            RegistroActividad.ACCION_EDITAR,
            instance,
            cambios={
                "estado": {
                    "antes": estado_anterior,
                    "despues": nuevo_estado,
                },
            },
            descripcion=mensaje,
        )
        serializer = self.get_serializer(instance)
        return Response(
            {"success": True, "message": mensaje, "cotizacion": serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="autorizar")
    @transaction.atomic
    def autorizar(self, request, pk=None):
        instance = self.get_object()
        if instance.estado == Cotizacion.ESTADO_CONVERTIDA:
            return Response(
                {
                    "success": False,
                    "message": (
                        "La cotización ya está vinculada a un proyecto y no "
                        "puede autorizarse manualmente."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._cambiar_estado(
            request,
            instance,
            Cotizacion.ESTADO_AUTORIZADA,
            "Cotización autorizada correctamente.",
        )

    @action(detail=True, methods=["post"], url_path="cancelar")
    @transaction.atomic
    def cancelar(self, request, pk=None):
        instance = self.get_object()
        if instance.estado == Cotizacion.ESTADO_CONVERTIDA:
            return Response(
                {
                    "success": False,
                    "message": (
                        "No se puede cancelar una cotización vinculada a un "
                        "proyecto. Primero debe retirarse del proyecto."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._cambiar_estado(
            request,
            instance,
            Cotizacion.ESTADO_CANCELADA,
            "Cotización cancelada correctamente.",
        )

    @action(detail=True, methods=["post"], url_path="reabrir")
    @transaction.atomic
    def reabrir(self, request, pk=None):
        instance = self.get_object()
        if instance.estado != Cotizacion.ESTADO_CANCELADA:
            return Response(
                {
                    "success": False,
                    "message": "Solo una cotización cancelada puede reabrirse.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self._cambiar_estado(
            request,
            instance,
            Cotizacion.ESTADO_PENDIENTE,
            "Cotización reabierta y enviada a pendientes.",
        )


class ConceptoCotizacionViewSet(ActivityLoggingMixin, viewsets.ModelViewSet):
    queryset = (
        ConceptoCotizacion.objects
        .select_related("cotizacion", "cotizacion__cliente", "catalogo")
        .order_by("id")
    )
    serializer_class = ConceptoCotizacionSerializer
    permission_classes = [EsLecturaOAdministrador]
    search_fields = ["descripcion", "cotizacion__codigo", "catalogo__descripcion"]
    filterset_fields = ["cotizacion", "unidad", "catalogo"]
    ordering_fields = ["descripcion", "cantidad", "precio_unitario", "total"]


class ConceptoCatalogoViewSet(BaseModelViewSet):
    queryset = ConceptoCatalogo.objects.all().order_by("descripcion", "unidad")
    serializer_class = ConceptoCatalogoSerializer

    def get_queryset(self):
        return super().get_queryset().annotate(
            cantidad_usos=Count("usos"),
        )
    permission_classes = [EsLecturaOAdministrador]
    search_fields = ["descripcion"]
    filterset_fields = ["unidad", "activo"]
    ordering_fields = [
        "descripcion",
        "unidad",
        "precio_unitario",
        "fecha_creacion",
        "fecha_actualizacion",
    ]
