from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from usuarios.models import RegistroActividad
from usuarios.permissions import EsDueno
from usuarios.services import (
    capturar_campos,
    comparar_capturas,
    registrar_actividad,
)


class ActivityLoggingMixin:
    """Registra crear, editar y eliminar sin alterar los serializers."""

    def _activity_manager(self, model):
        return getattr(model, "all_objects", model._default_manager)

    def _activity_instance(self, model, pk):
        return self._activity_manager(model).filter(pk=pk).first()

    def registrar_actividad(
        self,
        accion,
        instance,
        *,
        cambios=None,
        descripcion="",
    ):
        return registrar_actividad(
            usuario=self.request.user,
            accion=accion,
            instance=instance,
            cambios=cambios,
            descripcion=descripcion,
            request=self.request,
        )

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        pk = response.data.get("id") if isinstance(response.data, dict) else None

        if pk is not None:
            model = self.get_queryset().model
            instance = self._activity_instance(model, pk)
            if instance is not None:
                cambios = {
                    campo: {"antes": None, "despues": valor}
                    for campo, valor in capturar_campos(instance).items()
                }
                self.registrar_actividad(
                    RegistroActividad.ACCION_CREAR,
                    instance,
                    cambios=cambios,
                )

        return response

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        pk = instance.pk
        campos = list(request.data.keys())
        antes = capturar_campos(instance, campos)
        response = super().update(request, *args, **kwargs)
        model = self.get_queryset().model
        actualizado = self._activity_instance(model, pk)

        if actualizado is not None:
            despues = capturar_campos(actualizado, campos)
            cambios = comparar_capturas(antes, despues)
            if cambios:
                self.registrar_actividad(
                    RegistroActividad.ACCION_EDITAR,
                    actualizado,
                    cambios=cambios,
                )

        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        accion = (
            RegistroActividad.ACCION_ELIMINAR
            if hasattr(instance, "eliminado")
            else RegistroActividad.ACCION_ELIMINAR_DEFINITIVO
        )
        self.registrar_actividad(
            accion,
            instance,
        )
        return response


class BaseModelViewSet(ActivityLoggingMixin, viewsets.ModelViewSet):
    """
    ViewSet reutilizable para modelos que heredan de AuditableModel.

    Incluye:
    - Auditoría automática.
    - Historial de actividad.
    - Soft delete.
    - Listado de eliminados.
    - Restauración.
    - Eliminación definitiva para el rol DUENO.
    """

    def get_permissions(self):
        if self.action == "eliminar_definitivo":
            return [EsDueno()]

        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action in {
            "eliminados",
            "restaurar",
            "eliminar_definitivo",
        }:
            model = queryset.model
            return model.all_objects.all()

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            creado_por=self.request.user,
            modificado_por=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(
            modificado_por=self.request.user,
        )

    def perform_destroy(self, instance):
        instance.modificado_por = self.request.user
        instance.save(update_fields=["modificado_por", "fecha_actualizacion"])
        instance.delete()

    @action(
        detail=False,
        methods=["get"],
        url_path="eliminados",
    )
    def eliminados(self, request):
        queryset = (
            self.get_queryset()
            .filter(eliminado=True)
            .order_by("-fecha_actualizacion")
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path="restaurar",
    )
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

        instance.modificado_por = request.user
        instance.save(
            update_fields=["modificado_por", "fecha_actualizacion"],
        )
        instance.restaurar()
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

    @action(
        detail=True,
        methods=["delete"],
        url_path="eliminar-definitivo",
    )
    def eliminar_definitivo(self, request, pk=None):
        instance = self.get_object()

        if not instance.eliminado:
            return Response(
                {
                    "success": False,
                    "message": (
                        "El registro debe enviarse primero a la papelera."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.registrar_actividad(
            RegistroActividad.ACCION_ELIMINAR_DEFINITIVO,
            instance,
        )
        instance.hard_delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
