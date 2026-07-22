from datetime import date, datetime
from decimal import Decimal
from pathlib import PurePath
from uuid import UUID

from django.core.files import File
from django.db.models import Model

from .models import RegistroActividad


CAMPOS_SENSIBLES = {
    "password",
    "password_confirm",
    "current_password",
    "new_password",
    "confirm_password",
    "contraseña",
}

CAMPOS_AUDITORIA = {
    "creado_por",
    "modificado_por",
    "fecha_creacion",
    "fecha_actualizacion",
    "activo",
    "eliminado",
}


def normalizar_valor(value):
    if isinstance(value, Model):
        return {
            "id": value.pk,
            "texto": str(value),
        }

    if hasattr(value, "name") and isinstance(value, File):
        return value.name or None

    if hasattr(value, "name") and hasattr(value, "storage"):
        return value.name or None

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, PurePath):
        return str(value)

    if isinstance(value, dict):
        return {
            str(key): normalizar_valor(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [normalizar_valor(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def capturar_campos(instance, nombres_campos=None):
    if not instance or not hasattr(instance, "_meta"):
        return {}

    nombres_solicitados = set(nombres_campos or [])
    capturados = {}

    for field in instance._meta.concrete_fields:
        nombre = field.name

        if nombre in CAMPOS_SENSIBLES or nombre in CAMPOS_AUDITORIA:
            continue

        if nombres_solicitados and nombre not in nombres_solicitados:
            continue

        if field.is_relation:
            valor = getattr(instance, field.attname, None)
        else:
            valor = getattr(instance, nombre, None)

        capturados[nombre] = normalizar_valor(valor)

    return capturados


def comparar_capturas(antes, despues):
    cambios = {}

    for campo in sorted(set(antes) | set(despues)):
        valor_anterior = antes.get(campo)
        valor_nuevo = despues.get(campo)

        if valor_anterior != valor_nuevo:
            cambios[campo] = {
                "antes": valor_anterior,
                "despues": valor_nuevo,
            }

    return cambios


def obtener_ruta_objeto(instance):
    if not instance or not hasattr(instance, "_meta"):
        return ""

    etiqueta = instance._meta.label_lower

    if etiqueta == "clientes.clientepotencial":
        return "/clientes"

    if etiqueta == "cotizaciones.cotizacion":
        return f"/cotizaciones/{instance.pk}"

    if etiqueta == "cotizaciones.conceptocotizacion":
        return f"/cotizaciones/{instance.cotizacion_id}"

    if etiqueta == "cotizaciones.conceptocatalogo":
        return "/cotizaciones"

    if etiqueta == "proyectos.proyecto":
        return f"/proyectos/{instance.pk}"

    if etiqueta == "cobranza.pago":
        return "/cobros"

    if etiqueta in {"contabilidad.gasto", "contabilidad.categoriagasto"}:
        return "/libro"

    if etiqueta == "evidencias.evidencia":
        cotizacion = getattr(instance, "cotizacion", None)
        proyecto_id = None

        if cotizacion is not None:
            try:
                proyecto_id = cotizacion.proyecto.pk
            except Exception:
                proyecto_id = None

        if proyecto_id:
            return f"/proyectos/{proyecto_id}"

        cotizacion_id = getattr(instance, "cotizacion_id", None)
        if cotizacion_id:
            return f"/cotizaciones/{cotizacion_id}"

    if etiqueta == "auth.user":
        return "/usuarios"

    return ""


def obtener_ip(request):
    if request is None:
        return None

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def registrar_actividad(
    *,
    usuario,
    accion,
    instance=None,
    descripcion="",
    cambios=None,
    ruta=None,
    request=None,
    modelo=None,
    modelo_etiqueta=None,
    objeto_id=None,
    objeto_repr=None,
):
    if instance is not None and hasattr(instance, "_meta"):
        modelo = modelo or instance._meta.label_lower
        modelo_etiqueta = modelo_etiqueta or str(
            instance._meta.verbose_name,
        ).capitalize()
        objeto_id = objeto_id if objeto_id is not None else instance.pk
        objeto_repr = objeto_repr or str(instance)
        ruta = ruta if ruta is not None else obtener_ruta_objeto(instance)

    modelo = modelo or "sistema"
    modelo_etiqueta = modelo_etiqueta or "Sistema"
    objeto_repr = objeto_repr or modelo_etiqueta
    ruta = ruta or ""

    if not descripcion:
        etiqueta_accion = dict(RegistroActividad.ACCIONES).get(
            accion,
            accion,
        )
        descripcion = f"{etiqueta_accion} {modelo_etiqueta}: {objeto_repr}"

    return RegistroActividad.objects.create(
        usuario=usuario if getattr(usuario, "is_authenticated", False) else None,
        accion=accion,
        modelo=modelo,
        modelo_etiqueta=modelo_etiqueta[:100],
        objeto_id=str(objeto_id or "")[:64],
        objeto_repr=str(objeto_repr)[:255],
        descripcion=descripcion,
        cambios=normalizar_valor(cambios or {}),
        ruta=ruta[:255],
        ip=obtener_ip(request),
        user_agent=(
            request.META.get("HTTP_USER_AGENT", "")[:1000]
            if request is not None
            else ""
        ),
    )
