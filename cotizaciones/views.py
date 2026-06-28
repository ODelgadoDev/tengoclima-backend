from rest_framework import viewsets

from .models import Cotizacion, ConceptoCotizacion
from .serializers import CotizacionSerializer, ConceptoCotizacionSerializer
from usuarios.permissions import EsLecturaOAdministrador


class CotizacionViewSet(viewsets.ModelViewSet):
    queryset = Cotizacion.objects.all().order_by('-fecha_creacion')
    serializer_class = CotizacionSerializer
    permission_classes = [EsLecturaOAdministrador]


class ConceptoCotizacionViewSet(viewsets.ModelViewSet):
    queryset = ConceptoCotizacion.objects.all()
    serializer_class = ConceptoCotizacionSerializer
    permission_classes = [EsLecturaOAdministrador]