from django.db import transaction
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import BaseModelViewSet
from cotizaciones.models import Cotizacion
from usuarios.models import RegistroActividad
from usuarios.permissions import EsLecturaOAdministrador

from .models import Proyecto
from .serializers import (
    ProyectoDetalleSerializer,
    ProyectoSerializer,
    VincularCotizacionSerializer,
)


def cotizaciones_prefetch_queryset():
    return (
        Cotizacion.objects
        .select_related("cliente", "proyecto")
        .prefetch_related("pagos", "conceptos", "facturas")
        .order_by("-fecha_creacion")
    )


class ProyectoViewSet(BaseModelViewSet):
    queryset = Proyecto.objects.all()
    serializer_class = ProyectoSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_queryset(self):
        return (
            super().get_queryset()
            .select_related("cliente", "responsable")
            .prefetch_related(
                Prefetch(
                    "cotizaciones",
                    queryset=cotizaciones_prefetch_queryset(),
                ),
            )
            .order_by("-fecha_creacion")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProyectoDetalleSerializer
        return ProyectoSerializer

    search_fields = [
        "nombre",
        "responsable__username",
        "responsable__first_name",
        "responsable__last_name",
        "notas",
        "cliente__nombre_solicitante",
        "cliente__empresa",
        "cotizaciones__codigo",
        "cotizaciones__descripcion",
        "cotizaciones__conceptos__descripcion",
    ]
    filterset_fields = [
        "estado",
        "responsable",
        "cliente",
        "cotizaciones",
    ]
    ordering_fields = [
        "nombre",
        "responsable",
        "cliente",
        "fecha_inicio",
        "fecha_fin_estimada",
        "fecha_fin_real",
        "estado",
        "fecha_creacion",
        "fecha_actualizacion",
    ]

    def _validar_cotizacion(self, cotizacion, proyecto):
        if cotizacion.eliminado or not cotizacion.activo:
            raise ValidationError(
                {"cotizacion": "La cotización seleccionada no está activa."},
            )
        if cotizacion.estado != Cotizacion.ESTADO_AUTORIZADA:
            raise ValidationError(
                {"cotizacion": "Solo puedes vincular cotizaciones autorizadas."},
            )
        if cotizacion.cliente_id != proyecto.cliente_id:
            raise ValidationError(
                {
                    "cotizacion": (
                        "La cotización y el proyecto deben pertenecer al "
                        "mismo cliente."
                    ),
                },
            )
        if cotizacion.proyecto_id is not None:
            if cotizacion.proyecto_id == proyecto.pk:
                raise ValidationError(
                    {"cotizacion": "La cotización ya pertenece a este proyecto."},
                )
            raise ValidationError(
                {"cotizacion": "La cotización ya pertenece a otro proyecto."},
            )

    def _registrar_vinculo(self, proyecto, cotizacion, antes, despues):
        self.registrar_actividad(
            RegistroActividad.ACCION_EDITAR,
            cotizacion,
            cambios={
                "proyecto": {
                    "antes": antes,
                    "despues": despues,
                },
            },
            descripcion=(
                f"Cotización {cotizacion.codigo} vinculada al proyecto "
                f"{proyecto.nombre}."
                if despues is not None
                else (
                    f"Cotización {cotizacion.codigo} retirada del proyecto "
                    f"{proyecto.nombre}."
                )
            ),
        )
        self.registrar_actividad(
            RegistroActividad.ACCION_EDITAR,
            proyecto,
            cambios={
                "cotizaciones": {
                    "cotizacion": cotizacion.pk,
                    "codigo": cotizacion.codigo,
                    "accion": "AGREGAR" if despues is not None else "RETIRAR",
                },
            },
        )

    @transaction.atomic
    def perform_create(self, serializer):
        proyecto = serializer.save(
            creado_por=self.request.user,
            modificado_por=self.request.user,
        )
        cotizaciones = getattr(
            serializer,
            "cotizaciones_para_vincular",
            [],
        )

        for seleccionada in cotizaciones:
            cotizacion = (
                Cotizacion.all_objects
                .select_for_update()
                .select_related("cliente", "proyecto")
                .get(pk=seleccionada.pk)
            )
            self._validar_cotizacion(cotizacion, proyecto)
            cotizacion.proyecto = proyecto
            cotizacion.modificado_por = self.request.user
            cotizacion.save(
                update_fields=[
                    "proyecto",
                    "modificado_por",
                    "fecha_actualizacion",
                ],
            )
            self._registrar_vinculo(
                proyecto,
                cotizacion,
                None,
                proyecto.pk,
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="agregar-cotizacion",
    )
    @transaction.atomic
    def agregar_cotizacion(self, request, pk=None):
        proyecto = (
            Proyecto.all_objects
            .select_for_update()
            .select_related("cliente")
            .get(pk=self.get_object().pk)
        )
        payload = VincularCotizacionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        seleccionada = payload.validated_data["cotizacion"]
        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .select_related("cliente", "proyecto")
            .get(pk=seleccionada.pk)
        )
        self._validar_cotizacion(cotizacion, proyecto)

        cotizacion.proyecto = proyecto
        cotizacion.modificado_por = request.user
        cotizacion.save(
            update_fields=[
                "proyecto",
                "modificado_por",
                "fecha_actualizacion",
            ],
        )
        self._registrar_vinculo(
            proyecto,
            cotizacion,
            None,
            proyecto.pk,
        )

        actualizado = self.get_queryset().get(pk=proyecto.pk)
        return Response(
            {
                "success": True,
                "message": "Cotización agregada al proyecto correctamente.",
                "proyecto": ProyectoDetalleSerializer(
                    actualizado,
                    context=self.get_serializer_context(),
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="retirar-cotizacion",
    )
    @transaction.atomic
    def retirar_cotizacion(self, request, pk=None):
        proyecto = (
            Proyecto.all_objects
            .select_for_update()
            .get(pk=self.get_object().pk)
        )
        payload = VincularCotizacionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        seleccionada = payload.validated_data["cotizacion"]
        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .filter(
                pk=seleccionada.pk,
                proyecto_id=proyecto.pk,
            )
            .first()
        )

        if cotizacion is None:
            return Response(
                {
                    "success": False,
                    "message": "La cotización no pertenece a este proyecto.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cotizacion.proyecto = None
        cotizacion.modificado_por = request.user
        cotizacion.save(
            update_fields=[
                "proyecto",
                "modificado_por",
                "fecha_actualizacion",
            ],
        )
        self._registrar_vinculo(
            proyecto,
            cotizacion,
            proyecto.pk,
            None,
        )

        actualizado = self.get_queryset().get(pk=proyecto.pk)
        return Response(
            {
                "success": True,
                "message": "Cotización retirada del proyecto correctamente.",
                "proyecto": ProyectoDetalleSerializer(
                    actualizado,
                    context=self.get_serializer_context(),
                ).data,
            },
            status=status.HTTP_200_OK,
        )
