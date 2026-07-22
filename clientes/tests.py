from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from usuarios.models import PerfilUsuario

from .models import ClientePotencial


class ClientesSinEstadoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin-clientes",
            password="PasswordSegura123!",
        )

        perfil = self.user.perfilusuario
        perfil.rol = PerfilUsuario.ROL_ADMINISTRADOR
        perfil.activo = True
        perfil.requiere_cambio_contrasena = False
        perfil.save(
            update_fields=[
                "rol",
                "activo",
                "requiere_cambio_contrasena",
                "fecha_actualizacion",
            ],
        )

        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.user)

    def test_crear_cliente_sin_estado(self):
        response = self.client_api.post(
            "/api/clientes/clientes/",
            {
                "nombre_solicitante": "Cliente sin autorización",
                "empresa": "Empresa",
                "telefono": "6140000000",
                "direccion": "Chihuahua",
                "descripcion": "Cliente directo",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            getattr(response, "data", None),
        )
        self.assertNotIn("estado", response.data)
        self.assertTrue(
            ClientePotencial.objects.filter(
                nombre_solicitante="Cliente sin autorización",
            ).exists(),
        )
