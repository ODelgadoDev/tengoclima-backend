from rest_framework import viewsets

from .models import CategoriaGasto, Gasto
from .serializers import (
    CategoriaGastoSerializer,
    GastoSerializer
)


class CategoriaGastoViewSet(viewsets.ModelViewSet):
    queryset = CategoriaGasto.objects.all().order_by('nombre')
    serializer_class = CategoriaGastoSerializer


class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all().order_by('-fecha_gasto')
    serializer_class = GastoSerializer