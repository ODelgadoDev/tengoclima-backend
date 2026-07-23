from django.utils import timezone
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from usuarios.permissions import EsUsuarioActivo

from .models import Notificacion
from .serializers import NotificacionSerializer
from .services import sincronizar_alertas_proyectos


class NotificacionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NotificacionSerializer
    permission_classes = [EsUsuarioActivo]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["titulo", "mensaje", "tipo"]
    ordering_fields = ["fecha_creacion", "leida", "tipo", "nivel"]
    ordering = ["-fecha_creacion"]

    def get_queryset(self):
        queryset = Notificacion.objects.select_related("actor").filter(
            usuario=self.request.user,
        )
        leida = self.request.query_params.get("leida")
        tipo = self.request.query_params.get("tipo")

        if leida is not None:
            valor = leida.lower()
            if valor in {"1", "true", "si", "sí"}:
                queryset = queryset.filter(leida=True)
            elif valor in {"0", "false", "no"}:
                queryset = queryset.filter(leida=False)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        return queryset

    def list(self, request, *args, **kwargs):
        sincronizar_alertas_proyectos(request.user)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="resumen")
    def resumen(self, request):
        sincronizar_alertas_proyectos(request.user)
        queryset = self.get_queryset()
        ultimas = queryset[:5]
        return Response(
            {
                "total": queryset.count(),
                "no_leidas": queryset.filter(leida=False).count(),
                "ultimas": self.get_serializer(ultimas, many=True).data,
            },
        )

    @action(detail=True, methods=["post"], url_path="marcar-leida")
    def marcar_leida(self, request, pk=None):
        instance = self.get_object()
        if not instance.leida:
            instance.leida = True
            instance.fecha_lectura = timezone.now()
            instance.save(update_fields=["leida", "fecha_lectura"])
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=["post"], url_path="marcar-no-leida")
    def marcar_no_leida(self, request, pk=None):
        instance = self.get_object()
        if instance.leida:
            instance.leida = False
            instance.fecha_lectura = None
            instance.save(update_fields=["leida", "fecha_lectura"])
        return Response(self.get_serializer(instance).data)

    @action(detail=False, methods=["post"], url_path="marcar-todas-leidas")
    def marcar_todas_leidas(self, request):
        actualizadas = self.get_queryset().filter(leida=False).update(
            leida=True,
            fecha_lectura=timezone.now(),
        )
        return Response(
            {
                "success": True,
                "message": "Notificaciones marcadas como leídas.",
                "actualizadas": actualizadas,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["delete"], url_path="eliminar-leidas")
    def eliminar_leidas(self, request):
        eliminadas, _ = self.get_queryset().filter(leida=True).delete()
        return Response(
            {
                "success": True,
                "message": "Notificaciones leídas eliminadas.",
                "eliminadas": eliminadas,
            },
            status=status.HTTP_200_OK,
        )
