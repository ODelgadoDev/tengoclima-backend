from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone

from usuarios.models import PerfilUsuario

from .models import Notificacion


ROLES_GESTION = [
    PerfilUsuario.ROL_DUENO,
    PerfilUsuario.ROL_ADMINISTRADOR,
]


def _actor_valido(actor):
    if actor is not None and getattr(actor, "is_authenticated", False):
        return actor
    return None


def _usuario_habilitado(usuario):
    if usuario is None or not usuario.is_active:
        return False

    try:
        return usuario.perfilusuario.activo
    except PerfilUsuario.DoesNotExist:
        return False


def usuarios_gestion():
    return list(
        User.objects.select_related("perfilusuario").filter(
            is_active=True,
            perfilusuario__activo=True,
            perfilusuario__rol__in=ROLES_GESTION,
        ),
    )


def usuarios_para_proyecto(proyecto):
    usuarios = {usuario.pk: usuario for usuario in usuarios_gestion()}

    responsable = getattr(proyecto, "responsable", None)
    if _usuario_habilitado(responsable):
        usuarios[responsable.pk] = responsable

    return list(usuarios.values())


def usuarios_para_cotizacion(cotizacion):
    proyecto = getattr(cotizacion, "proyecto", None)
    if proyecto is not None:
        return usuarios_para_proyecto(proyecto)
    return usuarios_gestion()


def crear_notificacion(
    *,
    usuario,
    tipo,
    titulo,
    mensaje,
    ruta="",
    nivel=Notificacion.NIVEL_INFO,
    actor=None,
    modelo="",
    objeto_id="",
    clave="",
):
    if not _usuario_habilitado(usuario):
        return None

    actor = _actor_valido(actor)
    defaults = {
        "actor": actor,
        "tipo": tipo,
        "nivel": nivel,
        "titulo": titulo[:180],
        "mensaje": mensaje,
        "ruta": ruta[:255],
        "modelo": modelo[:100],
        "objeto_id": str(objeto_id or "")[:64],
    }

    if clave:
        try:
            notificacion, _ = Notificacion.objects.get_or_create(
                usuario=usuario,
                clave=clave[:255],
                defaults=defaults,
            )
            return notificacion
        except IntegrityError:
            return Notificacion.objects.filter(
                usuario=usuario,
                clave=clave[:255],
            ).first()

    return Notificacion.objects.create(
        usuario=usuario,
        clave="",
        **defaults,
    )


def crear_para_usuarios(
    usuarios,
    *,
    excluir=None,
    **datos,
):
    excluir_id = getattr(excluir, "pk", None)
    creadas = []
    vistos = set()

    for usuario in usuarios:
        if usuario.pk in vistos or usuario.pk == excluir_id:
            continue
        vistos.add(usuario.pk)
        notificacion = crear_notificacion(usuario=usuario, **datos)
        if notificacion is not None:
            creadas.append(notificacion)

    return creadas


def notificar_usuario_creado(usuario_objetivo, actor=None):
    nombre = usuario_objetivo.get_full_name().strip() or usuario_objetivo.username

    crear_notificacion(
        usuario=usuario_objetivo,
        actor=actor,
        tipo=Notificacion.TIPO_USUARIO_CREADO,
        nivel=Notificacion.NIVEL_INFO,
        titulo="Tu cuenta fue creada",
        mensaje=(
            "Tu cuenta de TENGOCLIMA ya está disponible. "
            "Debes cambiar la contraseña temporal al iniciar sesión."
        ),
        ruta="/perfil",
        modelo="auth.user",
        objeto_id=usuario_objetivo.pk,
    )

    crear_para_usuarios(
        usuarios_gestion(),
        excluir=actor,
        actor=actor,
        tipo=Notificacion.TIPO_USUARIO_CREADO,
        nivel=Notificacion.NIVEL_INFO,
        titulo="Usuario creado",
        mensaje=f"Se creó la cuenta de {nombre}.",
        ruta="/usuarios",
        modelo="auth.user",
        objeto_id=usuario_objetivo.pk,
    )


def notificar_usuario_activado(usuario_objetivo, actor=None):
    nombre = usuario_objetivo.get_full_name().strip() or usuario_objetivo.username

    crear_notificacion(
        usuario=usuario_objetivo,
        actor=actor,
        tipo=Notificacion.TIPO_USUARIO_ACTIVADO,
        nivel=Notificacion.NIVEL_EXITO,
        titulo="Cuenta activada",
        mensaje="Tu cuenta de TENGOCLIMA fue activada nuevamente.",
        ruta="/perfil",
        modelo="auth.user",
        objeto_id=usuario_objetivo.pk,
    )

    crear_para_usuarios(
        usuarios_gestion(),
        excluir=actor,
        actor=actor,
        tipo=Notificacion.TIPO_USUARIO_ACTIVADO,
        nivel=Notificacion.NIVEL_EXITO,
        titulo="Usuario activado",
        mensaje=f"Se activó la cuenta de {nombre}.",
        ruta="/usuarios",
        modelo="auth.user",
        objeto_id=usuario_objetivo.pk,
    )


def notificar_usuario_desactivado(usuario_objetivo, actor=None):
    nombre = usuario_objetivo.get_full_name().strip() or usuario_objetivo.username
    crear_para_usuarios(
        usuarios_gestion(),
        excluir=actor,
        actor=actor,
        tipo=Notificacion.TIPO_USUARIO_DESACTIVADO,
        nivel=Notificacion.NIVEL_ADVERTENCIA,
        titulo="Usuario desactivado",
        mensaje=f"Se desactivó la cuenta de {nombre}.",
        ruta="/usuarios",
        modelo="auth.user",
        objeto_id=usuario_objetivo.pk,
    )


def sincronizar_alertas_proyectos(usuario):
    if not _usuario_habilitado(usuario):
        return 0

    from proyectos.models import Proyecto

    hoy = timezone.localdate()
    limite = hoy + timedelta(days=3)
    terminales = [
        Proyecto.ESTADO_FINALIZADO,
        Proyecto.ESTADO_FACTURADO,
        Proyecto.ESTADO_PAGADO,
    ]

    queryset = Proyecto.objects.select_related(
        "cliente",
        "responsable",
    ).filter(
        activo=True,
        eliminado=False,
        fecha_fin_estimada__isnull=False,
    ).exclude(estado__in=terminales)

    try:
        es_gestion = usuario.perfilusuario.rol in ROLES_GESTION
    except PerfilUsuario.DoesNotExist:
        es_gestion = False

    if not es_gestion:
        queryset = queryset.filter(responsable=usuario)

    creadas = 0
    for proyecto in queryset.filter(fecha_fin_estimada__lte=limite):
        fecha = proyecto.fecha_fin_estimada
        if fecha < hoy:
            dias = (hoy - fecha).days
            notificacion = crear_notificacion(
                usuario=usuario,
                tipo=Notificacion.TIPO_PROYECTO_ATRASADO,
                nivel=Notificacion.NIVEL_ERROR,
                titulo="Proyecto atrasado",
                mensaje=(
                    f"{proyecto.nombre} venció hace {dias} "
                    f"día{'s' if dias != 1 else ''}."
                ),
                ruta=f"/proyectos/{proyecto.pk}",
                modelo="proyectos.proyecto",
                objeto_id=proyecto.pk,
                clave=(
                    f"proyecto-atrasado:{proyecto.pk}:"
                    f"{fecha.isoformat()}"
                ),
            )
        else:
            dias = (fecha - hoy).days
            if dias == 0:
                detalle = "vence hoy"
            elif dias == 1:
                detalle = "vence mañana"
            else:
                detalle = f"vence en {dias} días"

            notificacion = crear_notificacion(
                usuario=usuario,
                tipo=Notificacion.TIPO_PROYECTO_PROXIMO,
                nivel=Notificacion.NIVEL_ADVERTENCIA,
                titulo="Proyecto próximo a vencer",
                mensaje=f"{proyecto.nombre} {detalle}.",
                ruta=f"/proyectos/{proyecto.pk}",
                modelo="proyectos.proyecto",
                objeto_id=proyecto.pk,
                clave=(
                    f"proyecto-proximo:{proyecto.pk}:"
                    f"{fecha.isoformat()}"
                ),
            )

        if notificacion is not None:
            creadas += 1

    return creadas
