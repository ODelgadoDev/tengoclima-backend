from decimal import Decimal
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from clientes.models import ClientePotencial
from cotizaciones.models import ConceptoCotizacion, Cotizacion
from usuarios.models import PerfilUsuario

from .models import FacturaDocumento, Pago


class FacturasCobranzaV2Tests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()

        self.user = User.objects.create_user(
            username="admin-facturas",
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
            nombre_solicitante="Cliente facturas",
            empresa="Empresa facturas",
            telefono="6140000000",
            descripcion="",
        )
        self.cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            codigo="COT-FAC-001",
            descripcion="Cotización para facturación",
            estado=Cotizacion.ESTADO_AUTORIZADA,
        )
        ConceptoCotizacion.objects.create(
            cotizacion=self.cotizacion,
            descripcion="Trabajo completo",
            unidad="SERV",
            cantidad=Decimal("1.00"),
            precio_unitario=Decimal("1000.00"),
        )
        self.cotizacion.refresh_from_db()
        self.assertEqual(self.cotizacion.total, Decimal("1160.00"))

    def tearDown(self):
        self.media_override.disable()
        self.media_dir.cleanup()

    def pdf(self, nombre="factura.pdf"):
        return SimpleUploadedFile(
            nombre,
            b"%PDF-1.4\n% archivo de prueba\n",
            content_type="application/pdf",
        )

    def crear_factura(self, folio, importe):
        response = self.api.post(
            "/api/cobranza/facturas/",
            {
                "cotizacion": self.cotizacion.pk,
                "folio": folio,
                "archivo_pdf": self.pdf(f"{folio}.pdf"),
                "importe": str(importe),
                "fecha_emision": timezone.localdate().isoformat(),
                "observaciones": "Factura de prueba",
            },
            format="multipart",
        )
        self.assertEqual(
            response.status_code,
            201,
            getattr(response, "data", None),
        )
        return FacturaDocumento.objects.get(pk=response.data["id"])

    def test_facturacion_parcial_y_total(self):
        self.crear_factura("FAC-PARCIAL", Decimal("580.00"))
        self.cotizacion.refresh_from_db()
        self.assertEqual(
            self.cotizacion.estado_facturacion,
            "FACTURADA_PARCIAL",
        )
        self.assertEqual(self.cotizacion.total_facturado, Decimal("580.00"))
        self.assertEqual(self.cotizacion.saldo_por_facturar, Decimal("580.00"))

        self.crear_factura("FAC-RESTANTE", Decimal("580.00"))
        self.cotizacion.refresh_from_db()
        self.assertEqual(self.cotizacion.estado_facturacion, "FACTURADA")
        self.assertEqual(self.cotizacion.total_facturado, Decimal("1160.00"))

    def test_no_permite_sobrefacturar(self):
        self.crear_factura("FAC-UNO", Decimal("800.00"))
        response = self.api.post(
            "/api/cobranza/facturas/",
            {
                "cotizacion": self.cotizacion.pk,
                "folio": "FAC-DOS",
                "archivo_pdf": self.pdf("fac-dos.pdf"),
                "importe": "400.00",
                "fecha_emision": timezone.localdate().isoformat(),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("importe", response.data.get("errors", {}))

    def test_factura_pendiente_no_registra_pago(self):
        factura = self.crear_factura("FAC-PENDIENTE", Decimal("1160.00"))
        self.assertEqual(factura.estado, FacturaDocumento.ESTADO_PENDIENTE)
        self.assertEqual(Pago.objects.count(), 0)
        self.cotizacion.refresh_from_db()
        self.assertEqual(self.cotizacion.estado_facturacion, "FACTURADA")
        self.assertEqual(self.cotizacion.estado_cobranza, "PENDIENTE")

    def test_marcar_factura_pagada_crea_pago(self):
        factura = self.crear_factura("FAC-50", Decimal("580.00"))
        response = self.api.post(
            f"/api/cobranza/facturas/{factura.pk}/marcar-pagada/",
            {
                "fecha_pago": timezone.localdate().isoformat(),
                "metodo_pago": "TRANSFERENCIA",
                "referencia": "TRANSFER-001",
                "notas": "Pago del cincuenta por ciento",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)

        factura.refresh_from_db()
        self.cotizacion.refresh_from_db()
        pago = Pago.objects.get(factura=factura)
        self.assertEqual(factura.estado, FacturaDocumento.ESTADO_PAGADA)
        self.assertEqual(pago.monto, Decimal("580.00"))
        self.assertEqual(self.cotizacion.total_pagado, Decimal("580.00"))
        self.assertEqual(self.cotizacion.estado_cobranza, "PARCIAL")

    def test_pago_vinculado_sincroniza_estado_de_factura(self):
        factura = self.crear_factura("FAC-PAGO-DIRECTO", Decimal("300.00"))
        response = self.api.post(
            "/api/cobranza/pagos/",
            {
                "cotizacion": self.cotizacion.pk,
                "factura": factura.pk,
                "monto": "300.00",
                "metodo_pago": "EFECTIVO",
                "fecha_pago": timezone.localdate().isoformat(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        factura.refresh_from_db()
        self.assertEqual(factura.estado, FacturaDocumento.ESTADO_PAGADA)
        self.assertEqual(factura.saldo_pendiente, Decimal("0.00"))

    def test_cancelar_y_reabrir_factura(self):
        factura = self.crear_factura("FAC-CANCELAR", Decimal("500.00"))
        response = self.api.post(
            f"/api/cobranza/facturas/{factura.pk}/cancelar/",
            {"motivo": "Se sustituirá por otra factura."},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        factura.refresh_from_db()
        self.cotizacion.refresh_from_db()
        self.assertEqual(factura.estado, FacturaDocumento.ESTADO_CANCELADA)
        self.assertEqual(self.cotizacion.total_facturado, Decimal("0.00"))

        response = self.api.post(
            f"/api/cobranza/facturas/{factura.pk}/reabrir/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        factura.refresh_from_db()
        self.assertEqual(factura.estado, FacturaDocumento.ESTADO_PENDIENTE)

    def test_no_elimina_factura_con_pagos(self):
        factura = self.crear_factura("FAC-CON-PAGO", Decimal("200.00"))
        Pago.objects.create(
            cotizacion=self.cotizacion,
            factura=factura,
            monto=Decimal("100.00"),
            metodo_pago="EFECTIVO",
            fecha_pago=timezone.localdate(),
            creado_por=self.user,
            modificado_por=self.user,
        )
        response = self.api.delete(
            f"/api/cobranza/facturas/{factura.pk}/",
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertTrue(FacturaDocumento.objects.filter(pk=factura.pk).exists())

    def test_rechaza_archivo_que_no_es_pdf(self):
        response = self.api.post(
            "/api/cobranza/facturas/",
            {
                "cotizacion": self.cotizacion.pk,
                "folio": "FAC-NO-PDF",
                "archivo_pdf": SimpleUploadedFile(
                    "imagen.jpg",
                    b"contenido de imagen",
                    content_type="image/jpeg",
                ),
                "importe": "100.00",
                "fecha_emision": timezone.localdate().isoformat(),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("archivo_pdf", response.data.get("errors", {}))
