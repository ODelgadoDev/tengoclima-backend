from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from cobranza.models import FacturaDocumento, Pago
from cotizaciones.models import Cotizacion
from evidencias.models import Evidencia
from proyectos.models import Proyecto

from .models import Notificacion
from .services import (
    crear_notificacion,
    crear_para_usuarios,
    usuarios_para_cotizacion,
    usuarios_para_proyecto,
)


def _valor_anterior(sender, instance, campo):
    if not instance.pk:
        return None

    anterior = sender.all_objects.filter(pk=instance.pk).values(campo).first()
    if anterior is None:
        return None
    return anterior.get(campo)


@receiver(pre_save, sender=Proyecto)
def recordar_responsable_proyecto(sender, instance, **kwargs):
    instance._responsable_anterior_id = _valor_anterior(
        sender,
        instance,
        "responsable_id",
    )


@receiver(post_save, sender=Proyecto)
def notificar_proyecto_asignado(sender, instance, created, **kwargs):
    if instance.eliminado or not instance.activo or not instance.responsable_id:
        return

    anterior = getattr(instance, "_responsable_anterior_id", None)
    if not created and anterior == instance.responsable_id:
        return

    actor = instance.modificado_por or instance.creado_por
    crear_notificacion(
        usuario=instance.responsable,
        actor=actor,
        tipo=Notificacion.TIPO_PROYECTO_ASIGNADO,
        nivel=Notificacion.NIVEL_INFO,
        titulo="Proyecto asignado",
        mensaje=f"Se te asignó el proyecto {instance.nombre}.",
        ruta=f"/proyectos/{instance.pk}",
        modelo="proyectos.proyecto",
        objeto_id=instance.pk,
    )


@receiver(pre_save, sender=Cotizacion)
def recordar_estado_cotizacion(sender, instance, **kwargs):
    instance._estado_anterior_notificacion = _valor_anterior(
        sender,
        instance,
        "estado",
    )


@receiver(post_save, sender=Cotizacion)
def notificar_estado_cotizacion(sender, instance, created, **kwargs):
    if created or instance.eliminado or not instance.activo:
        return

    anterior = getattr(instance, "_estado_anterior_notificacion", None)
    if anterior == instance.estado:
        return

    if instance.estado == Cotizacion.ESTADO_AUTORIZADA:
        tipo = Notificacion.TIPO_COTIZACION_AUTORIZADA
        nivel = Notificacion.NIVEL_EXITO
        titulo = "Cotización autorizada"
        mensaje = f"La cotización {instance.codigo} fue autorizada."
    elif instance.estado == Cotizacion.ESTADO_CANCELADA:
        tipo = Notificacion.TIPO_COTIZACION_CANCELADA
        nivel = Notificacion.NIVEL_ADVERTENCIA
        titulo = "Cotización cancelada"
        mensaje = f"La cotización {instance.codigo} fue cancelada."
    else:
        return

    actor = instance.modificado_por or instance.creado_por
    crear_para_usuarios(
        usuarios_para_cotizacion(instance),
        excluir=actor,
        actor=actor,
        tipo=tipo,
        nivel=nivel,
        titulo=titulo,
        mensaje=mensaje,
        ruta=f"/cotizaciones/{instance.pk}",
        modelo="cotizaciones.cotizacion",
        objeto_id=instance.pk,
    )


@receiver(pre_save, sender=FacturaDocumento)
def recordar_estado_factura(sender, instance, **kwargs):
    instance._estado_anterior_notificacion = _valor_anterior(
        sender,
        instance,
        "estado",
    )


@receiver(post_save, sender=FacturaDocumento)
def notificar_factura(sender, instance, created, **kwargs):
    if instance.eliminado or not instance.activo:
        return

    actor = instance.modificado_por or instance.creado_por
    destinatarios = usuarios_para_cotizacion(instance.cotizacion)

    if created:
        crear_para_usuarios(
            destinatarios,
            excluir=actor,
            actor=actor,
            tipo=Notificacion.TIPO_FACTURA_CREADA,
            nivel=Notificacion.NIVEL_INFO,
            titulo="Factura cargada",
            mensaje=(
                f"Se cargó la factura {instance.folio} para "
                f"{instance.cotizacion.codigo}."
            ),
            ruta=f"/cotizaciones/{instance.cotizacion_id}",
            modelo="cobranza.facturadocumento",
            objeto_id=instance.pk,
        )
        return

    anterior = getattr(instance, "_estado_anterior_notificacion", None)
    if (
        anterior != instance.estado
        and instance.estado == FacturaDocumento.ESTADO_PAGADA
    ):
        crear_para_usuarios(
            destinatarios,
            excluir=actor,
            actor=actor,
            tipo=Notificacion.TIPO_FACTURA_PAGADA,
            nivel=Notificacion.NIVEL_EXITO,
            titulo="Factura pagada",
            mensaje=f"La factura {instance.folio} quedó pagada.",
            ruta=f"/cotizaciones/{instance.cotizacion_id}",
            modelo="cobranza.facturadocumento",
            objeto_id=instance.pk,
        )


@receiver(post_save, sender=Pago)
def notificar_pago_registrado(sender, instance, created, **kwargs):
    if not created or instance.eliminado or not instance.activo:
        return

    actor = instance.creado_por or instance.modificado_por
    folio = f" para la factura {instance.factura.folio}" if instance.factura_id else ""
    crear_para_usuarios(
        usuarios_para_cotizacion(instance.cotizacion),
        excluir=actor,
        actor=actor,
        tipo=Notificacion.TIPO_PAGO_REGISTRADO,
        nivel=Notificacion.NIVEL_EXITO,
        titulo="Pago registrado",
        mensaje=(
            f"Se registró un pago de ${instance.monto:,.2f} en "
            f"{instance.cotizacion.codigo}{folio}."
        ),
        ruta=f"/cotizaciones/{instance.cotizacion_id}",
        modelo="cobranza.pago",
        objeto_id=instance.pk,
    )


@receiver(post_save, sender=Evidencia)
def notificar_archivo_nuevo(sender, instance, created, **kwargs):
    if not created or instance.eliminado or not instance.activo:
        return

    if instance.cotizacion_id:
        cotizacion = instance.cotizacion
        destinatarios = usuarios_para_cotizacion(cotizacion)
        ruta = f"/cotizaciones/{cotizacion.pk}"
        origen = cotizacion.codigo
    elif instance.proyecto_id:
        proyecto = instance.proyecto
        destinatarios = usuarios_para_proyecto(proyecto)
        ruta = f"/proyectos/{proyecto.pk}"
        origen = proyecto.nombre
    else:
        return

    actor = instance.creado_por or instance.modificado_por
    tipo_archivo = instance.get_tipo_display().lower()
    crear_para_usuarios(
        destinatarios,
        excluir=actor,
        actor=actor,
        tipo=Notificacion.TIPO_ARCHIVO_NUEVO,
        nivel=Notificacion.NIVEL_INFO,
        titulo="Archivo nuevo",
        mensaje=f"Se agregó {tipo_archivo} en {origen}.",
        ruta=ruta,
        modelo="evidencias.evidencia",
        objeto_id=instance.pk,
    )
