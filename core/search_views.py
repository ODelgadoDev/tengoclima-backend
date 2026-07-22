from django.contrib.auth.models import User
from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from clientes.models import ClientePotencial
from cotizaciones.models import Cotizacion
from proyectos.models import Proyecto
from usuarios.models import PerfilUsuario
from usuarios.permissions import EsUsuarioActivo

from .search_serializers import BusquedaGlobalSerializer


MIN_CARACTERES = 2
LIMITE_DEFAULT = 5
LIMITE_MAXIMO = 10


def _texto_corto(value, max_length=120):
    texto = (value or "").strip().replace("\r", " ").replace("\n", " ")
    if len(texto) <= max_length:
        return texto
    return f"{texto[: max_length - 1].rstrip()}…"


def _limite_seguro(value):
    try:
        limite = int(value)
    except (TypeError, ValueError):
        return LIMITE_DEFAULT
    return max(1, min(limite, LIMITE_MAXIMO))


class BusquedaGlobalView(APIView):
    permission_classes = [EsUsuarioActivo]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="q",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Texto a buscar. Requiere al menos 2 caracteres.",
            ),
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Máximo por grupo. Valor permitido: 1 a 10.",
            ),
        ],
        responses={200: BusquedaGlobalSerializer},
        summary="Búsqueda global",
        description=(
            "Busca clientes, cotizaciones y proyectos activos. "
            "Dueño y Administrador también reciben usuarios activos."
        ),
    )
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        limite = _limite_seguro(request.query_params.get("limit"))

        if len(query) < MIN_CARACTERES:
            return Response(
                {
                    "query": query,
                    "min_caracteres": MIN_CARACTERES,
                    "total": 0,
                    "clientes": [],
                    "cotizaciones": [],
                    "proyectos": [],
                    "usuarios": [],
                },
            )

        clientes_qs = (
            ClientePotencial.objects
            .filter(activo=True)
            .filter(
                Q(nombre_solicitante__icontains=query)
                | Q(empresa__icontains=query)
                | Q(telefono__icontains=query)
                | Q(direccion__icontains=query)
                | Q(descripcion__icontains=query)
            )
            .order_by("nombre_solicitante", "empresa")[:limite]
        )

        cotizaciones_qs = (
            Cotizacion.objects
            .select_related("cliente")
            .filter(activo=True)
            .filter(
                Q(codigo__icontains=query)
                | Q(descripcion__icontains=query)
                | Q(estimado_tiempo__icontains=query)
                | Q(cliente__nombre_solicitante__icontains=query)
                | Q(cliente__empresa__icontains=query)
                | Q(conceptos__descripcion__icontains=query)
            )
            .distinct()
            .order_by("-fecha_actualizacion")[:limite]
        )

        proyectos_qs = (
            Proyecto.objects
            .select_related(
                "cotizacion",
                "cotizacion__cliente",
                "responsable",
            )
            .filter(activo=True)
            .filter(
                Q(nombre__icontains=query)
                | Q(notas__icontains=query)
                | Q(estado__icontains=query)
                | Q(responsable__username__icontains=query)
                | Q(responsable__first_name__icontains=query)
                | Q(responsable__last_name__icontains=query)
                | Q(cotizacion__codigo__icontains=query)
                | Q(cotizacion__descripcion__icontains=query)
                | Q(cotizacion__cliente__nombre_solicitante__icontains=query)
                | Q(cotizacion__cliente__empresa__icontains=query)
                | Q(cotizacion__conceptos__descripcion__icontains=query)
            )
            .distinct()
            .order_by("-fecha_actualizacion")[:limite]
        )

        clientes = [
            {
                "id": cliente.id,
                "tipo": "CLIENTE",
                "titulo": cliente.nombre_solicitante,
                "subtitulo": cliente.empresa or cliente.telefono,
                "descripcion": _texto_corto(
                    " · ".join(
                        part
                        for part in [cliente.telefono, cliente.direccion]
                        if part
                    ),
                ),
                "estado": "ACTIVO",
                "ruta": "/clientes",
            }
            for cliente in clientes_qs
        ]

        cotizaciones = [
            {
                "id": cotizacion.id,
                "tipo": "COTIZACION",
                "titulo": cotizacion.codigo,
                "subtitulo": " · ".join(
                    part
                    for part in [
                        cotizacion.cliente.nombre_solicitante,
                        cotizacion.cliente.empresa,
                    ]
                    if part
                ),
                "descripcion": _texto_corto(cotizacion.descripcion),
                "estado": cotizacion.estado,
                "ruta": f"/cotizaciones/{cotizacion.id}",
            }
            for cotizacion in cotizaciones_qs
        ]

        proyectos = [
            {
                "id": proyecto.id,
                "tipo": "PROYECTO",
                "titulo": proyecto.nombre,
                "subtitulo": " · ".join(
                    part
                    for part in [
                        proyecto.cotizacion.codigo,
                        proyecto.cotizacion.cliente.nombre_solicitante,
                    ]
                    if part
                ),
                "descripcion": _texto_corto(
                    proyecto.notas or proyecto.cotizacion.descripcion,
                ),
                "estado": proyecto.estado,
                "ruta": f"/proyectos/{proyecto.id}",
            }
            for proyecto in proyectos_qs
        ]

        usuarios = []
        perfil_actor = request.user.perfilusuario
        if perfil_actor.rol in {
            PerfilUsuario.ROL_DUENO,
            PerfilUsuario.ROL_ADMINISTRADOR,
        }:
            usuarios_qs = (
                User.objects
                .select_related("perfilusuario")
                .filter(
                    is_active=True,
                    perfilusuario__activo=True,
                )
                .filter(
                    Q(username__icontains=query)
                    | Q(first_name__icontains=query)
                    | Q(last_name__icontains=query)
                    | Q(email__icontains=query)
                    | Q(perfilusuario__rol__icontains=query)
                )
                .order_by("first_name", "last_name", "username")[:limite]
            )

            usuarios = [
                {
                    "id": usuario.id,
                    "tipo": "USUARIO",
                    "titulo": usuario.get_full_name().strip() or usuario.username,
                    "subtitulo": usuario.email or usuario.username,
                    "descripcion": usuario.perfilusuario.get_rol_display(),
                    "estado": "ACTIVO",
                    "ruta": "/usuarios",
                }
                for usuario in usuarios_qs
            ]

        data = {
            "query": query,
            "min_caracteres": MIN_CARACTERES,
            "clientes": clientes,
            "cotizaciones": cotizaciones,
            "proyectos": proyectos,
            "usuarios": usuarios,
        }
        data["total"] = sum(
            len(data[key])
            for key in [
                "clientes",
                "cotizaciones",
                "proyectos",
                "usuarios",
            ]
        )

        serializer = BusquedaGlobalSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)
