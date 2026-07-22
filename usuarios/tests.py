from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import PerfilUsuario, RegistroActividad


class AdministracionUsuariosTests(APITestCase):
    def setUp(self):
        self.dueno = User.objects.create_user(
            username="dueno",
            email="dueno@example.com",
            password="PasswordSegura123!",
        )
        self.dueno.perfilusuario.rol = PerfilUsuario.ROL_DUENO
        self.dueno.perfilusuario.save()

        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="PasswordSegura123!",
        )
        self.admin.perfilusuario.rol = PerfilUsuario.ROL_ADMINISTRADOR
        self.admin.perfilusuario.save()

    def test_dueno_puede_crear_usuario(self):
        self.client.force_authenticate(self.dueno)
        response = self.client.post(
            "/api/auth/administracion-usuarios/",
            {
                "username": "alfredito",
                "first_name": "Alfredo",
                "last_name": "Prueba",
                "email": "alfredito@example.com",
                "rol": PerfilUsuario.ROL_AYUDANTE,
                "telefono": "6140000000",
                "password": "TemporalSegura123!",
                "password_confirm": "TemporalSegura123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        usuario = User.objects.get(username="alfredito")
        self.assertTrue(usuario.perfilusuario.requiere_cambio_contrasena)
        self.assertTrue(
            RegistroActividad.objects.filter(
                usuario=self.dueno,
                accion=RegistroActividad.ACCION_CREAR,
            ).exists(),
        )

    def test_admin_no_puede_crear_dueno(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/auth/administracion-usuarios/",
            {
                "username": "otro-dueno",
                "email": "otro@example.com",
                "rol": PerfilUsuario.ROL_DUENO,
                "password": "TemporalSegura123!",
                "password_confirm": "TemporalSegura123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_no_se_puede_desactivar_a_si_mismo(self):
        self.client.force_authenticate(self.dueno)
        response = self.client.delete(
            f"/api/auth/administracion-usuarios/{self.dueno.pk}/",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cambio_contrasena_limpia_bandera(self):
        self.admin.perfilusuario.requiere_cambio_contrasena = True
        self.admin.perfilusuario.save()
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            "/api/auth/perfil/cambiar-contrasena/",
            {
                "current_password": "PasswordSegura123!",
                "new_password": "NuevaPasswordSegura123!",
                "confirm_password": "NuevaPasswordSegura123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin.refresh_from_db()
        self.admin.perfilusuario.refresh_from_db()
        self.assertTrue(self.admin.check_password("NuevaPasswordSegura123!"))
        self.assertFalse(self.admin.perfilusuario.requiere_cambio_contrasena)
