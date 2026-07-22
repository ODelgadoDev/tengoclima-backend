from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PerfilUsuario


@receiver(post_save, sender=User)
def crear_o_sincronizar_perfil(sender, instance, created, **kwargs):
    perfil, _ = PerfilUsuario.objects.get_or_create(
        usuario=instance,
        defaults={
            "rol": (
                PerfilUsuario.ROL_DUENO
                if instance.is_superuser
                else PerfilUsuario.ROL_AYUDANTE
            ),
            "activo": instance.is_active,
        },
    )

    if perfil.activo != instance.is_active:
        PerfilUsuario.objects.filter(pk=perfil.pk).update(
            activo=instance.is_active,
        )


@receiver(post_save, sender=PerfilUsuario)
def sincronizar_usuario_activo(sender, instance, **kwargs):
    if instance.usuario.is_active != instance.activo:
        User.objects.filter(pk=instance.usuario_id).update(
            is_active=instance.activo,
        )
