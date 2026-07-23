from django.contrib.auth.models import User

from notificaciones.services import (
    notificar_usuario_activado,
    notificar_usuario_creado,
    notificar_usuario_desactivado,
)
from django.db import transaction
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PerfilUsuario, RegistroActividad
from .permissions import (
    EsAdministradorODueno,
    EsPerfilActivo,
    EsUsuarioActivo,
)
from .serializers import (
    CambiarContrasenaSerializer,
    PerfilPropioSerializer,
    RegistroActividadSerializer,
    RestablecerContrasenaSerializer,
    UsuarioAdministracionSerializer,
    UsuarioResponsableSerializer,
)
from .services import registrar_actividad


class PerfilActualView(APIView):
    permission_classes = [EsPerfilActivo]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_perfil(self, request):
        perfil, _ = PerfilUsuario.objects.select_related("usuario").get_or_create(
            usuario=request.user,
        )
        return perfil

    def get(self, request):
        serializer = PerfilPropioSerializer(
            self.get_perfil(request),
            context={"request": request},
        )
        return Response(serializer.data)

    @transaction.atomic
    def patch(self, request):
        perfil = self.get_perfil(request)
        usuario = perfil.usuario
        antes = {
            "first_name": usuario.first_name,
            "last_name": usuario.last_name,
            "email": usuario.email,
            "telefono": perfil.telefono,
            "foto_perfil": perfil.foto_perfil.name if perfil.foto_perfil else None,
        }

        serializer = PerfilPropioSerializer(
            perfil,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        perfil = serializer.save()

        despues = {
            "first_name": perfil.usuario.first_name,
            "last_name": perfil.usuario.last_name,
            "email": perfil.usuario.email,
            "telefono": perfil.telefono,
            "foto_perfil": perfil.foto_perfil.name if perfil.foto_perfil else None,
        }
        cambios = {
            campo: {"antes": antes[campo], "despues": despues[campo]}
            for campo in antes
            if antes[campo] != despues[campo]
        }

        if cambios:
            registrar_actividad(
                usuario=request.user,
                accion=RegistroActividad.ACCION_EDITAR,
                instance=request.user,
                descripcion="Actualizó su perfil.",
                cambios=cambios,
                ruta="/perfil",
                request=request,
            )

        return Response(serializer.data)


class CambiarContrasenaView(APIView):
    permission_classes = [EsPerfilActivo]

    @transaction.atomic
    def post(self, request):
        serializer = CambiarContrasenaSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        registrar_actividad(
            usuario=request.user,
            accion=RegistroActividad.ACCION_CAMBIAR_CONTRASENA,
            instance=request.user,
            descripcion="Cambió su contraseña.",
            ruta="/perfil",
            request=request,
        )

        return Response(
            {
                "success": True,
                "message": "Contraseña actualizada correctamente.",
            },
            status=status.HTTP_200_OK,
        )


class UsuariosActivosView(ListAPIView):
    serializer_class = UsuarioResponsableSerializer
    permission_classes = [EsUsuarioActivo]
    pagination_class = None

    def get_queryset(self):
        return (
            PerfilUsuario.objects
            .select_related("usuario")
            .filter(
                activo=True,
                usuario__is_active=True,
                requiere_cambio_contrasena=False,
            )
            .order_by(
                "usuario__first_name",
                "usuario__last_name",
                "usuario__username",
            )
        )


class UsuarioAdministracionViewSet(viewsets.ModelViewSet):
    permission_classes = [EsAdministradorODueno]
    serializer_class = UsuarioAdministracionSerializer
    http_method_names = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
    ]
    search_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "perfilusuario__telefono",
    ]
    filterset_fields = [
        "is_active",
        "perfilusuario__activo",
        "perfilusuario__rol",
    ]
    ordering_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "date_joined",
        "last_login",
    ]

    def get_queryset(self):
        return (
            User.objects
            .select_related("perfilusuario")
            .all()
            .order_by("first_name", "last_name", "username")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()

        registrar_actividad(
            usuario=request.user,
            accion=RegistroActividad.ACCION_CREAR,
            instance=usuario,
            descripcion=f"Creó al usuario {usuario.username}.",
            cambios={
                "rol": {
                    "antes": None,
                    "despues": usuario.perfilusuario.rol,
                },
                "activo": {
                    "antes": None,
                    "despues": True,
                },
            },
            ruta="/usuarios",
            request=request,
        )
        notificar_usuario_creado(usuario, actor=request.user)

        output = self.get_serializer(usuario)
        headers = self.get_success_headers(output.data)
        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        perfil = instance.perfilusuario
        antes = {
            "username": instance.username,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "email": instance.email,
            "rol": perfil.rol,
            "telefono": perfil.telefono,
        }

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        perfil = usuario.perfilusuario
        despues = {
            "username": usuario.username,
            "first_name": usuario.first_name,
            "last_name": usuario.last_name,
            "email": usuario.email,
            "rol": perfil.rol,
            "telefono": perfil.telefono,
        }
        cambios = {
            campo: {"antes": antes[campo], "despues": despues[campo]}
            for campo in antes
            if antes[campo] != despues[campo]
        }

        if cambios:
            registrar_actividad(
                usuario=request.user,
                accion=RegistroActividad.ACCION_EDITAR,
                instance=usuario,
                descripcion=f"Editó al usuario {usuario.username}.",
                cambios=cambios,
                ruta="/usuarios",
                request=request,
            )

        return Response(self.get_serializer(usuario).data)

    def _validar_objetivo(self, request, usuario_objetivo):
        actor = request.user
        actor_perfil = actor.perfilusuario
        objetivo_perfil = usuario_objetivo.perfilusuario

        if usuario_objetivo.pk == actor.pk:
            return "No puedes desactivar tu propia cuenta."

        if (
            actor_perfil.rol == PerfilUsuario.ROL_ADMINISTRADOR
            and objetivo_perfil.rol == PerfilUsuario.ROL_DUENO
        ):
            return "Un Administrador no puede modificar a un Dueño."

        if (
            objetivo_perfil.rol == PerfilUsuario.ROL_DUENO
            and PerfilUsuario.objects.filter(
                rol=PerfilUsuario.ROL_DUENO,
                activo=True,
                usuario__is_active=True,
            ).count() <= 1
        ):
            return "No se puede desactivar al último Dueño activo."

        return None

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        usuario = self.get_object()
        error = self._validar_objetivo(request, usuario)
        if error:
            return Response(
                {"detail": error},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not usuario.is_active or not usuario.perfilusuario.activo:
            return Response(
                {"detail": "El usuario ya está desactivado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
        perfil = usuario.perfilusuario
        perfil.activo = False
        perfil.save(update_fields=["activo", "fecha_actualizacion"])

        registrar_actividad(
            usuario=request.user,
            accion=RegistroActividad.ACCION_DESACTIVAR,
            instance=usuario,
            descripcion=f"Desactivó al usuario {usuario.username}.",
            cambios={"activo": {"antes": True, "despues": False}},
            ruta="/usuarios",
            request=request,
        )
        notificar_usuario_desactivado(usuario, actor=request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="activar")
    @transaction.atomic
    def activar(self, request, pk=None):
        usuario = self.get_object()
        actor_perfil = request.user.perfilusuario

        if (
            actor_perfil.rol == PerfilUsuario.ROL_ADMINISTRADOR
            and usuario.perfilusuario.rol == PerfilUsuario.ROL_DUENO
        ):
            return Response(
                {"detail": "Un Administrador no puede modificar a un Dueño."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if usuario.is_active and usuario.perfilusuario.activo:
            return Response(
                {"detail": "El usuario ya está activo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        usuario.is_active = True
        usuario.save(update_fields=["is_active"])
        perfil = usuario.perfilusuario
        perfil.activo = True
        perfil.save(update_fields=["activo", "fecha_actualizacion"])

        registrar_actividad(
            usuario=request.user,
            accion=RegistroActividad.ACCION_ACTIVAR,
            instance=usuario,
            descripcion=f"Activó al usuario {usuario.username}.",
            cambios={"activo": {"antes": False, "despues": True}},
            ruta="/usuarios",
            request=request,
        )
        notificar_usuario_activado(usuario, actor=request.user)

        return Response(self.get_serializer(usuario).data)

    @action(detail=True, methods=["post"], url_path="desactivar")
    def desactivar(self, request, pk=None):
        return self.destroy(request, pk=pk)

    @action(
        detail=True,
        methods=["post"],
        url_path="restablecer-contrasena",
    )
    @transaction.atomic
    def restablecer_contrasena(self, request, pk=None):
        usuario = self.get_object()
        actor_perfil = request.user.perfilusuario

        if (
            actor_perfil.rol == PerfilUsuario.ROL_ADMINISTRADOR
            and usuario.perfilusuario.rol == PerfilUsuario.ROL_DUENO
        ):
            return Response(
                {"detail": "Un Administrador no puede modificar a un Dueño."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RestablecerContrasenaSerializer(
            data=request.data,
            context={"usuario": usuario},
        )
        serializer.is_valid(raise_exception=True)
        usuario.set_password(serializer.validated_data["password"])
        usuario.save(update_fields=["password"])

        perfil = usuario.perfilusuario
        perfil.requiere_cambio_contrasena = True
        perfil.save(
            update_fields=[
                "requiere_cambio_contrasena",
                "fecha_actualizacion",
            ],
        )

        registrar_actividad(
            usuario=request.user,
            accion=RegistroActividad.ACCION_RESTABLECER_CONTRASENA,
            instance=usuario,
            descripcion=f"Restableció la contraseña de {usuario.username}.",
            ruta="/usuarios",
            request=request,
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Contraseña temporal asignada. El usuario deberá "
                    "cambiarla al iniciar sesión."
                ),
            },
            status=status.HTTP_200_OK,
        )


class RegistroActividadListView(ListAPIView):
    serializer_class = RegistroActividadSerializer
    permission_classes = [EsUsuarioActivo]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "descripcion",
        "objeto_repr",
        "modelo_etiqueta",
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
    ]
    ordering_fields = ["fecha", "accion", "modelo"]
    ordering = ["-fecha"]

    def get_queryset(self):
        request = self.request
        queryset = RegistroActividad.objects.select_related("usuario")
        usuario_id = request.query_params.get("usuario")
        accion = request.query_params.get("accion")
        modelo = request.query_params.get("modelo")

        puede_administrar = (
            request.user.perfilusuario.rol
            in [
                PerfilUsuario.ROL_DUENO,
                PerfilUsuario.ROL_ADMINISTRADOR,
            ]
        )

        if usuario_id and puede_administrar:
            queryset = queryset.filter(usuario_id=usuario_id)
        else:
            queryset = queryset.filter(usuario=request.user)

        if accion:
            queryset = queryset.filter(accion=accion)

        if modelo:
            queryset = queryset.filter(modelo=modelo)

        return queryset
