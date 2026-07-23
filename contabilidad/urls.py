from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoriaGastoViewSet,
    GastoViewSet,
    LibroContableView,
    LibroExportarCsvView,
    LibroExportarExcelView,
    LibroResumenView,
)

router = DefaultRouter()
router.register(
    r"categorias-gasto",
    CategoriaGastoViewSet,
    basename="categorias-gasto",
)
router.register(
    r"gastos",
    GastoViewSet,
    basename="gastos",
)

urlpatterns = [
    path("libro/", LibroContableView.as_view(), name="libro-contable"),
    path(
        "libro/resumen/",
        LibroResumenView.as_view(),
        name="libro-resumen",
    ),
    path(
        "libro/exportar-excel/",
        LibroExportarExcelView.as_view(),
        name="libro-exportar-excel",
    ),
    path(
        "libro/exportar-csv/",
        LibroExportarCsvView.as_view(),
        name="libro-exportar-csv",
    ),
] + router.urls
