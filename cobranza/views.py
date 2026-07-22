from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from core.viewsets import BaseModelViewSet
from cotizaciones.models import Cotizacion
from usuarios.models import RegistroActividad
from usuarios.permissions import EsLecturaOAdministrador, EsUsuarioActivo

from .models import Pago
from .serializers import PagoDetalleSerializer, PagoSerializer


class PagoViewSet(BaseModelViewSet):
    queryset = (
        Pago.objects
        .select_related("cotizacion", "cotizacion__cliente")
        .order_by("-fecha_pago", "-fecha_creacion")
    )
    serializer_class = PagoSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PagoDetalleSerializer

        return PagoSerializer

    search_fields = [
        "referencia",
        "notas",
        "cotizacion__codigo",
        "cotizacion__descripcion",
        "cotizacion__cliente__nombre_solicitante",
        "cotizacion__cliente__empresa",
    ]
    filterset_fields = [
        "cotizacion",
        "metodo_pago",
        "fecha_pago",
    ]
    ordering_fields = [
        "monto",
        "metodo_pago",
        "fecha_pago",
        "fecha_creacion",
    ]

    @transaction.atomic
    def perform_create(self, serializer):
        cotizacion_validada = serializer.validated_data["cotizacion"]
        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .get(pk=cotizacion_validada.pk)
        )
        monto = serializer.validated_data["monto"]

        if cotizacion.eliminado or not cotizacion.activo:
            raise ValidationError(
                {"cotizacion": "La cotización seleccionada no está activa."},
            )

        if cotizacion.total <= 0:
            raise ValidationError(
                {
                    "cotizacion": (
                        "No se puede registrar un pago en una "
                        "cotización sin total."
                    ),
                },
            )

        if monto > cotizacion.saldo_pendiente:
            raise ValidationError(
                {
                    "monto": (
                        "El pago no puede ser mayor al saldo pendiente "
                        "de la cotización."
                    ),
                },
            )

        serializer.save(
            cotizacion=cotizacion,
            creado_por=self.request.user,
            modificado_por=self.request.user,
        )

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.instance
        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .get(pk=instance.cotizacion_id)
        )
        monto = serializer.validated_data.get("monto", instance.monto)
        disponible = cotizacion.saldo_pendiente + instance.monto

        if monto > disponible:
            raise ValidationError(
                {
                    "monto": (
                        "El pago no puede ser mayor al saldo disponible "
                        "de la cotización."
                    ),
                },
            )

        serializer.save(
            cotizacion=cotizacion,
            modificado_por=self.request.user,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="restaurar",
    )
    @transaction.atomic
    def restaurar(self, request, pk=None):
        instance = self.get_object()

        if not instance.eliminado:
            return Response(
                {
                    "success": False,
                    "message": "El registro no está eliminado.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .get(pk=instance.cotizacion_id)
        )

        if cotizacion.eliminado or not cotizacion.activo:
            return Response(
                {
                    "success": False,
                    "message": (
                        "No se puede restaurar el pago porque su "
                        "cotización no está activa."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if instance.monto > cotizacion.saldo_pendiente:
            return Response(
                {
                    "success": False,
                    "message": (
                        "No se puede restaurar el pago porque supera "
                        "el saldo pendiente actual."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.eliminado = False
        instance.activo = True
        instance.modificado_por = request.user
        instance.save(
            update_fields=[
                "eliminado",
                "activo",
                "modificado_por",
                "fecha_actualizacion",
            ],
        )

        self.registrar_actividad(
            RegistroActividad.ACCION_RESTAURAR,
            instance,
        )

        return Response(
            {
                "success": True,
                "message": "Registro restaurado correctamente.",
            },
            status=status.HTTP_200_OK,
        )


class PorCobrarView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        data = []
        cotizaciones = (
            Cotizacion.objects
            .select_related("cliente")
            .prefetch_related("pagos")
            .order_by("-fecha_creacion")
        )

        for cotizacion in cotizaciones:
            if cotizacion.saldo_pendiente > 0:
                data.append(
                    {
                        "id": cotizacion.id,
                        "codigo": cotizacion.codigo,
                        "cliente": cotizacion.cliente.nombre_solicitante,
                        "empresa": cotizacion.cliente.empresa,
                        "total": cotizacion.total,
                        "pagado": cotizacion.total_pagado,
                        "pendiente": cotizacion.saldo_pendiente,
                        "estado": cotizacion.estado_cobranza,
                    },
                )

        return Response(data)


class PagadosView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        data = []
        cotizaciones = (
            Cotizacion.objects
            .select_related("cliente")
            .prefetch_related("pagos")
            .order_by("-fecha_creacion")
        )

        for cotizacion in cotizaciones:
            if cotizacion.estado_cobranza == "PAGADO":
                data.append(
                    {
                        "id": cotizacion.id,
                        "codigo": cotizacion.codigo,
                        "cliente": cotizacion.cliente.nombre_solicitante,
                        "empresa": cotizacion.cliente.empresa,
                        "total": cotizacion.total,
                        "pagado": cotizacion.total_pagado,
                    },
                )

        return Response(data)
