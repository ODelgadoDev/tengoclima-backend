from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import FacturaDocumento, Pago
from .services import sincronizar_estado_factura


@receiver(pre_save, sender=Pago)
def recordar_factura_anterior(sender, instance, **kwargs):
    instance._factura_anterior_id = None
    if not instance.pk:
        return

    anterior = sender.all_objects.filter(pk=instance.pk).only("factura_id").first()
    if anterior is not None:
        instance._factura_anterior_id = anterior.factura_id


@receiver(post_save, sender=Pago)
def sincronizar_factura_por_pago(sender, instance, **kwargs):
    anterior_id = getattr(instance, "_factura_anterior_id", None)
    if anterior_id and anterior_id != instance.factura_id:
        sincronizar_estado_factura(anterior_id)

    if instance.factura_id:
        sincronizar_estado_factura(instance.factura_id)


@receiver(post_delete, sender=Pago)
def sincronizar_factura_al_borrar_pago(sender, instance, **kwargs):
    if instance.factura_id:
        sincronizar_estado_factura(instance.factura_id)


@receiver(pre_save, sender=FacturaDocumento)
def recordar_pdf_anterior(sender, instance, **kwargs):
    instance._pdf_anterior_name = None
    if not instance.pk:
        return

    anterior = (
        sender.all_objects
        .filter(pk=instance.pk)
        .only("archivo_pdf")
        .first()
    )
    if anterior is not None and anterior.archivo_pdf:
        instance._pdf_anterior_name = anterior.archivo_pdf.name


@receiver(post_save, sender=FacturaDocumento)
def eliminar_pdf_reemplazado(sender, instance, **kwargs):
    anterior = getattr(instance, "_pdf_anterior_name", None)
    actual = instance.archivo_pdf.name if instance.archivo_pdf else None
    if anterior and anterior != actual:
        instance.archivo_pdf.storage.delete(anterior)


@receiver(post_delete, sender=FacturaDocumento)
def eliminar_pdf_factura(sender, instance, **kwargs):
    archivo = instance.archivo_pdf
    if archivo and archivo.name:
        archivo.storage.delete(archivo.name)
