from django.urls import path
from .views import PerfilActualView

urlpatterns = [
    path('perfil/', PerfilActualView.as_view(), name='perfil-actual'),
]