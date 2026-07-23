from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Evidencia


@receiver(post_delete, sender=Evidencia)
def eliminar_archivo_fisico(sender, instance, **kwargs):
    """Limpia el almacenamiento solo cuando el registro se borra físicamente."""
    if not instance.archivo:
        return

    nombre = instance.archivo.name
    storage = instance.archivo.storage
    if nombre and storage.exists(nombre):
        storage.delete(nombre)
