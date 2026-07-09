from rest_framework import viewsets


class BaseModelViewSet(viewsets.ModelViewSet):

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
        instance.delete()