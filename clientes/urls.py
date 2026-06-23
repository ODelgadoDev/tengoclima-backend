from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClientePotencialViewSet

router = DefaultRouter()
router.register(r'clientes', ClientePotencialViewSet)

urlpatterns = [
    path('', include(router.urls)),
]