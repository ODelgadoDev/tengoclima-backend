from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/clientes/', include('clientes.urls')),
    path('api/cotizaciones/', include('cotizaciones.urls')),
    path('api/proyectos/', include('proyectos.urls')),
    path('api/cobranza/', include('cobranza.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/contabilidad/', include('contabilidad.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)