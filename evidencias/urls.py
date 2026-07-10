from rest_framework.routers import DefaultRouter

from .views import EvidenciaViewSet

router = DefaultRouter()

router.register(
    r'evidencias',
    EvidenciaViewSet,
    basename='evidencias'
)

urlpatterns = router.urls