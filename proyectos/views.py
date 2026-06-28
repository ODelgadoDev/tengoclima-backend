from rest_framework import viewsets

from .models import Proyecto
from .serializers import ProyectoSerializer
from usuarios.permissions import EsLecturaOAdministrador


class ProyectoViewSet(viewsets.ModelViewSet):
    queryset = Proyecto.objects.all().order_by('-fecha_creacion')
    serializer_class = ProyectoSerializer
    permission_classes = [EsLecturaOAdministrador]