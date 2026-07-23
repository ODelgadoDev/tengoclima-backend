from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import NotificacionViewSet


router = SimpleRouter()
router.register("", NotificacionViewSet, basename="notificacion")

urlpatterns = [
    path("", include(router.urls)),
]
