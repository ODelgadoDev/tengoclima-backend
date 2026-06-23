from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CotizacionViewSet, ConceptoCotizacionViewSet

router = DefaultRouter()
router.register(r'cotizaciones', CotizacionViewSet)
router.register(r'conceptos-cotizacion', ConceptoCotizacionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]