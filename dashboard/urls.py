from django.urls import path
from .views import DashboardResumenView, DashboardFinanzasView

urlpatterns = [
    path(
        'resumen/',
        DashboardResumenView.as_view(),
        name='dashboard-resumen'
    ),
    path(
        'finanzas/',
        DashboardFinanzasView.as_view(),
        name='dashboard-finanzas'
    ),
]