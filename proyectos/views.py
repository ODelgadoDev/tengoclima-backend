from django.db import transaction
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
)


class ProyectoViewSet(BaseModelViewSet):
    queryset = (
        Proyecto.objects
        .select_related(
            "cotizacion",
            "cotizacion__cliente",
            "responsable",
        )
        .order_by("-fecha_creacion")
    )
    serializer_class = ProyectoSerializer
    permission_classes = [EsLecturaOAdministrador]

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
        "cotizacion__codigo",
        "cotizacion__cliente__nombre_solicitante",
        "cotizacion__cliente__empresa",
    ]
    filterset_fields = [
        "estado",
        "responsable",
        "cotizacion",
    ]
    ordering_fields = [
        "nombre",
        "responsable",
        "fecha_inicio",
        "fecha_fin_estimada",
        "fecha_fin_real",
        "estado",
        "fecha_creacion",
        "fecha_actualizacion",
    ]

    @transaction.atomic
    def perform_create(self, serializer):
        cotizacion_validada = serializer.validated_data["cotizacion"]

        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .get(pk=cotizacion_validada.pk)
        )

        proyecto_existente = (
            Proyecto.all_objects
            .select_for_update()
            .filter(cotizacion_id=cotizacion.pk)
            .first()
        )

        if proyecto_existente:
            if proyecto_existente.eliminado:
                raise ValidationError(
                    {
                        "cotizacion": (
                            "Esta cotización ya pertenece a un proyecto "
                            "eliminado. Restaura ese proyecto desde la "
                            "papelera."
                        ),
                    },
                )

            raise ValidationError(
                {
                    "cotizacion": (
                        "Esta cotización ya fue convertida en proyecto."
                    ),
                },
            )

        if (
            cotizacion.eliminado
            or not cotizacion.activo
            or cotizacion.estado
            != Cotizacion.ESTADO_AUTORIZADA
        ):
            raise ValidationError(
                {
                    "cotizacion": (
                        "Solo una cotización activa y autorizada puede "
                        "convertirse en proyecto."
                    ),
                },
            )

        serializer.save(
            cotizacion=cotizacion,
            creado_por=self.request.user,
            modificado_por=self.request.user,
        )

        cotizacion.estado = Cotizacion.ESTADO_CONVERTIDA
        cotizacion.modificado_por = self.request.user
        cotizacion.save(
            update_fields=[
                "estado",
                "modificado_por",
                "fecha_actualizacion",
            ],
        )

    @transaction.atomic
    def perform_destroy(self, instance):
        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .get(pk=instance.cotizacion_id)
        )

        super().perform_destroy(instance)

        if cotizacion.estado == Cotizacion.ESTADO_CONVERTIDA:
            cotizacion.estado = Cotizacion.ESTADO_AUTORIZADA
            cotizacion.modificado_por = self.request.user
            cotizacion.save(
                update_fields=[
                    "estado",
                    "modificado_por",
                    "fecha_actualizacion",
                ],
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
                        "No se puede restaurar el proyecto porque su "
                        "cotización no está activa."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if cotizacion.estado != Cotizacion.ESTADO_AUTORIZADA:
            return Response(
                {
                    "success": False,
                    "message": (
                        "La cotización debe estar autorizada antes de "
                        "restaurar el proyecto."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        otro_proyecto_activo = (
            Proyecto.all_objects
            .select_for_update()
            .filter(
                cotizacion_id=cotizacion.pk,
                eliminado=False,
            )
            .exclude(pk=instance.pk)
            .exists()
        )

        if otro_proyecto_activo:
            return Response(
                {
                    "success": False,
                    "message": (
                        "La cotización ya pertenece a otro proyecto "
                        "activo."
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

        cotizacion.estado = Cotizacion.ESTADO_CONVERTIDA
        cotizacion.modificado_por = request.user
        cotizacion.save(
            update_fields=[
                "estado",
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
