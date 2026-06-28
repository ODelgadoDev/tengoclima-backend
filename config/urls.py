from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/clientes/', include('clientes.urls')),
    path('api/cotizaciones/', include('cotizaciones.urls')),
    path('api/proyectos/', include('proyectos.urls')),
    path('api/cobranza/', include('cobranza.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/contabilidad/', include('contabilidad.urls')),
    path('api/auth/', include('usuarios.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)