from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from clientes.models import ClientePotencial
from usuarios.models import PerfilUsuario

from .models import ConceptoCatalogo, ConceptoCotizacion, Cotizacion


class CotizacionesV2Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin-pruebas",
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

        self.cliente = ClientePotencial.objects.create(
            nombre_solicitante="Cliente prueba",
            telefono="6140000000",
            descripcion="",
        )
        self.cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            codigo="COT-V2-001",
            descripcion="Prueba",
        )

    def test_catalogo_reutiliza_datos_y_acepta_lote(self):
        catalogo = ConceptoCatalogo.objects.create(
            descripcion="Instalación por lote",
            unidad="LOTE",
            precio_unitario=Decimal("2500.00"),
        )

        response = self.client_api.post(
            "/api/cotizaciones/conceptos-cotizacion/",
            {
                "cotizacion": self.cotizacion.id,
                "catalogo": catalogo.id,
                "cantidad": "2.00",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            getattr(response, "data", None),
        )
        concepto = ConceptoCotizacion.objects.get(pk=response.data["id"])
        self.assertEqual(concepto.unidad, "LOTE")
        self.assertEqual(concepto.total, Decimal("5000.00"))

    def test_acciones_estado(self):
        response = self.client_api.post(
            f"/api/cotizaciones/cotizaciones/{self.cotizacion.id}/autorizar/",
            {},
            format="json",
        )
        self.assertEqual(
            response.status_code,
            200,
            getattr(response, "data", None),
        )

        self.cotizacion.refresh_from_db()
        self.assertEqual(
            self.cotizacion.estado,
            Cotizacion.ESTADO_AUTORIZADA,
        )

        response = self.client_api.post(
            f"/api/cotizaciones/cotizaciones/{self.cotizacion.id}/cancelar/",
            {},
            format="json",
        )
        self.assertEqual(
            response.status_code,
            200,
            getattr(response, "data", None),
        )

        self.cotizacion.refresh_from_db()
        self.assertEqual(
            self.cotizacion.estado,
            Cotizacion.ESTADO_CANCELADA,
        )

        response = self.client_api.post(
            f"/api/cotizaciones/cotizaciones/{self.cotizacion.id}/reabrir/",
            {},
            format="json",
        )
        self.assertEqual(
            response.status_code,
            200,
            getattr(response, "data", None),
        )

        self.cotizacion.refresh_from_db()
        self.assertEqual(
            self.cotizacion.estado,
            Cotizacion.ESTADO_PENDIENTE,
        )

    def test_catalogo_eliminados_conserva_conteo_de_usos(self):
        catalogo = ConceptoCatalogo.objects.create(
            descripcion="Concepto para papelera",
            unidad="SERV",
            precio_unitario=Decimal("800.00"),
        )
        ConceptoCotizacion.objects.create(
            cotizacion=self.cotizacion,
            catalogo=catalogo,
            descripcion=catalogo.descripcion,
            unidad=catalogo.unidad,
            cantidad=Decimal("1.00"),
            precio_unitario=catalogo.precio_unitario,
        )

        delete_response = self.client_api.delete(
            f"/api/cotizaciones/catalogo-conceptos/{catalogo.id}/",
        )
        self.assertEqual(
            delete_response.status_code,
            204,
            getattr(delete_response, "data", None),
        )

        response = self.client_api.get(
            "/api/cotizaciones/catalogo-conceptos/eliminados/",
        )
        self.assertEqual(
            response.status_code,
            200,
            getattr(response, "data", None),
        )
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["usos"], 1)

