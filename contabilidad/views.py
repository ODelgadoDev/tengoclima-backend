from rest_framework import viewsets

from .models import CategoriaGasto, Gasto
from .serializers import (
    CategoriaGastoSerializer,
    GastoSerializer
)

from usuarios.permissions import EsLecturaOAdministrador


class CategoriaGastoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaGasto.objects.all().order_by('nombre')
    serializer_class = CategoriaGastoSerializer
    permission_classes = [EsLecturaOAdministrador]


class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all().order_by('-fecha_gasto')
    serializer_class = GastoSerializer
    permission_classes = [EsLecturaOAdministrador]