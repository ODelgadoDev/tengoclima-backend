from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    FacturaDocumentoViewSet,
    PagadosView,
    PagoViewSet,
    PorCobrarView,
)

router = DefaultRouter()
router.register(r"pagos", PagoViewSet, basename="pagos")
router.register(r"facturas", FacturaDocumentoViewSet, basename="facturas")

urlpatterns = router.urls + [
    path("por-cobrar/", PorCobrarView.as_view(), name="por-cobrar"),
    path("pagados/", PagadosView.as_view(), name="pagados"),
]
