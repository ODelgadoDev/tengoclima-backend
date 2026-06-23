from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    ROL_DUENO = 'DUENO'
    ROL_ADMINISTRADOR = 'ADMINISTRADOR'
    ROL_AYUDANTE = 'AYUDANTE'

    ROLES = [
        (ROL_DUENO, 'Dueño'),
        (ROL_ADMINISTRADOR, 'Administrador'),
        (ROL_AYUDANTE, 'Ayudante'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, default=ROL_AYUDANTE)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.rol}"