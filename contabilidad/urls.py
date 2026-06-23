from rest_framework.routers import DefaultRouter

from .views import (
    CategoriaGastoViewSet,
    GastoViewSet
)

router = DefaultRouter()

router.register(
    r'categorias-gasto',
    CategoriaGastoViewSet,
    basename='categorias-gasto'
)

router.register(
    r'gastos',
    GastoViewSet,
    basename='gastos'
)

urlpatterns = router.urls