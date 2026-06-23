from rest_framework import viewsets
from .models import ClientePotencial
from .serializers import ClientePotencialSerializer


class ClientePotencialViewSet(viewsets.ModelViewSet):
    queryset = ClientePotencial.objects.all().order_by('-fecha_creacion')
    serializer_class = ClientePotencialSerializer