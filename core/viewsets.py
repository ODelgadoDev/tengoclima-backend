from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from usuarios.permissions import EsDueno


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet reutilizable para modelos que heredan de AuditableModel.

    Incluye:
    - Auditoría automática.
    - Soft delete.
    - Listado de eliminados.
    - Restauración.
    - Eliminación definitiva para el rol DUENO.
    """

    def get_permissions(self):
        if self.action == 'eliminar_definitivo':
            return [EsDueno()]

        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action in {
            'eliminados',
            'restaurar',
            'eliminar_definitivo',
        }:
            model = queryset.model
            return model.all_objects.all()

        return queryset

    def perform_create(self, serializer):
        serializer.save(
            creado_por=self.request.user,
            modificado_por=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(
            modificado_por=self.request.user
        )

    def perform_destroy(self, instance):
        instance.modificado_por = self.request.user
        instance.save(update_fields=['modificado_por', 'fecha_actualizacion'])
        instance.delete()

    @action(
        detail=False,
        methods=['get'],
        url_path='eliminados'
    )
    def eliminados(self, request):
        queryset = (
            self.get_queryset()
            .filter(eliminado=True)
            .order_by('-fecha_actualizacion')
        )

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        url_path='restaurar'
    )
    def restaurar(self, request, pk=None):
        instance = self.get_object()

        if not instance.eliminado:
            return Response(
                {
                    'success': False,
                    'message': 'El registro no está eliminado.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.modificado_por = request.user
        instance.restaurar()

        return Response(
            {
                'success': True,
                'message': 'Registro restaurado correctamente.'
            },
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['delete'],
        url_path='eliminar-definitivo'
    )
    def eliminar_definitivo(self, request, pk=None):
        instance = self.get_object()

        if not instance.eliminado:
            return Response(
                {
                    'success': False,
                    'message': (
                        'El registro debe enviarse primero a la papelera.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.hard_delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )