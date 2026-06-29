from rest_framework import viewsets

from .models import Proyecto
from .serializers import ProyectoSerializer
from usuarios.permissions import EsLecturaOAdministrador


class ProyectoViewSet(viewsets.ModelViewSet):
    queryset = Proyecto.objects.all().order_by('-fecha_creacion')
    serializer_class = ProyectoSerializer
    permission_classes = [EsLecturaOAdministrador]

    search_fields = [
        'nombre',
        'responsable',
        'notas',
        'cotizacion__codigo',
        'cotizacion__cliente__nombre_solicitante',
        'cotizacion__cliente__empresa',
    ]

    filterset_fields = [
        'estado',
        'responsable',
        'cotizacion',
    ]

    ordering_fields = [
        'nombre',
        'responsable',
        'fecha_inicio',
        'fecha_fin_estimada',
        'fecha_fin_real',
        'estado',
        'fecha_creacion',
        'fecha_actualizacion',
    ]