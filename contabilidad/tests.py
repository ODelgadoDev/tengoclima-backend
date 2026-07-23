from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from clientes.models import ClientePotencial
from cobranza.models import Pago
from cotizaciones.models import Cotizacion
from proyectos.models import Proyecto
from usuarios.models import PerfilUsuario

from .models import CategoriaGasto, Gasto


class LibroContableTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin-libro",
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

        self.api = APIClient()
        self.api.force_authenticate(user=self.user)

        self.cliente = ClientePotencial.objects.create(
            nombre_solicitante="Cliente contable",
            empresa="Empresa contable",
            telefono="6140000000",
            descripcion="",
        )
        self.proyecto = Proyecto.objects.create(
            cliente=self.cliente,
            nombre="Proyecto contable",
            responsable=self.user,
        )
        self.cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            proyecto=self.proyecto,
            codigo="COT-LIBRO-001",
            descripcion="Cotización del libro",
            subtotal=Decimal("1000.00"),
            iva=Decimal("160.00"),
            total=Decimal("1160.00"),
            estado=Cotizacion.ESTADO_AUTORIZADA,
        )
        self.pago = Pago.objects.create(
            cotizacion=self.cotizacion,
            monto=Decimal("580.00"),
            metodo_pago="TRANSFERENCIA",
            referencia="SPEI-001",
            fecha_pago=date(2026, 7, 20),
            creado_por=self.user,
            modificado_por=self.user,
        )
        self.categoria = CategoriaGasto.objects.create(
            nombre="Material",
            activo=True,
        )
        self.gasto = Gasto.objects.create(
            categoria=self.categoria,
            proyecto=self.proyecto,
            cotizacion=self.cotizacion,
            concepto="Compra de material",
            proveedor="Proveedor",
            monto=Decimal("232.00"),
            iva=Decimal("32.00"),
            metodo_pago="TRANSFERENCIA",
            fecha_gasto=date(2026, 7, 21),
            creado_por=self.user,
            modificado_por=self.user,
        )

    def test_libro_combina_ingresos_y_gastos(self):
        response = self.api.get("/api/contabilidad/libro/?page_size=100")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 2)
        tipos = {item["tipo"] for item in response.data["results"]}
        self.assertEqual(tipos, {"INGRESO", "GASTO"})
        self.assertEqual(
            Decimal(str(response.data["resumen"]["utilidad"])),
            Decimal("348.00"),
        )

    def test_filtros_por_proyecto_y_tipo(self):
        response = self.api.get(
            "/api/contabilidad/libro/",
            {
                "proyecto": self.proyecto.id,
                "tipo": "GASTO",
                "page_size": 100,
            },
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["tipo"], "GASTO")

    def test_resumen_calcula_iva(self):
        response = self.api.get("/api/contabilidad/libro/resumen/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            Decimal(str(response.data["iva_ingresos"])),
            Decimal("80.00"),
        )
        self.assertEqual(
            Decimal(str(response.data["iva_gastos"])),
            Decimal("32.00"),
        )
        self.assertEqual(
            Decimal(str(response.data["iva_neto"])),
            Decimal("48.00"),
        )

    def test_exporta_excel(self):
        response = self.api.get("/api/contabilidad/libro/exportar-excel/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "spreadsheetml.sheet",
            response["Content-Type"],
        )
        self.assertTrue(response.content.startswith(b"PK"))

    def test_exporta_csv(self):
        response = self.api.get("/api/contabilidad/libro/exportar-csv/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])
        self.assertIn("Compra de material", response.content.decode("utf-8"))

    def test_iva_no_puede_superar_monto(self):
        response = self.api.post(
            "/api/contabilidad/gastos/",
            {
                "categoria": self.categoria.id,
                "concepto": "Gasto inválido",
                "monto": "100.00",
                "iva": "120.00",
                "metodo_pago": "EFECTIVO",
                "fecha_gasto": "2026-07-20",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("iva", response.data.get("errors", {}))

    def test_rechaza_cotizacion_de_otro_proyecto(self):
        otro_proyecto = Proyecto.objects.create(
            cliente=self.cliente,
            nombre="Otro proyecto",
        )
        response = self.api.post(
            "/api/contabilidad/gastos/",
            {
                "categoria": self.categoria.id,
                "proyecto": otro_proyecto.id,
                "cotizacion": self.cotizacion.id,
                "concepto": "Gasto inconsistente",
                "monto": "100.00",
                "iva": "0.00",
                "metodo_pago": "EFECTIVO",
                "fecha_gasto": "2026-07-20",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("cotizacion", response.data.get("errors", {}))
