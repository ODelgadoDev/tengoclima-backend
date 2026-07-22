from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ConceptoCatalogoViewSet,
    ConceptoCotizacionViewSet,
    CotizacionViewSet,
)

router = DefaultRouter()
router.register(r"cotizaciones", CotizacionViewSet)
router.register(r"conceptos-cotizacion", ConceptoCotizacionViewSet)
router.register(r"catalogo-conceptos", ConceptoCatalogoViewSet)

urlpatterns = [path("", include(router.urls))]
