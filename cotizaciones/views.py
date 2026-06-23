from rest_framework import viewsets
from .models import Cotizacion, ConceptoCotizacion
from .serializers import CotizacionSerializer, ConceptoCotizacionSerializer


class CotizacionViewSet(viewsets.ModelViewSet):
    queryset = Cotizacion.objects.all().order_by('-fecha_creacion')
    serializer_class = CotizacionSerializer


class ConceptoCotizacionViewSet(viewsets.ModelViewSet):
    queryset = ConceptoCotizacion.objects.all()
    serializer_class = ConceptoCotizacionSerializer