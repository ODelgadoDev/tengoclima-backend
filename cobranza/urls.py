from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    PagoViewSet,
    PorCobrarView,
    PagadosView
)

router = DefaultRouter()

router.register(
    r'pagos',
    PagoViewSet,
    basename='pagos'
)

urlpatterns = router.urls + [
    path(
        'por-cobrar/',
        PorCobrarView.as_view(),
        name='por-cobrar'
    ),
    path(
        'pagados/',
        PagadosView.as_view(),
        name='pagados'
    ),
]