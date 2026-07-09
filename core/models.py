from django.conf import settings
from django.db import models


class AuditableQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(activo=True, eliminado=False)

    def eliminados(self):
        return self.filter(eliminado=True)


class AuditableManager(models.Manager):
    def get_queryset(self):
        return AuditableQuerySet(
            self.model,
            using=self._db
        ).filter(eliminado=False)

    def activos(self):
        return self.get_queryset().activos()

    def eliminados(self):
        return AuditableQuerySet(
            self.model,
            using=self._db
        ).eliminados()


class AuditableModel(models.Model):
    activo = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)

    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_creados'
    )

    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_modificados'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    objects = AuditableManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.eliminado = True
        self.activo = False
        self.save(update_fields=['eliminado', 'activo', 'fecha_actualizacion'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)