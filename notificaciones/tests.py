from datetime import timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from clientes.models import ClientePotencial
from cobranza.models import FacturaDocumento, Pago
from cotizaciones.models import Cotizacion
from evidencias.models import Evidencia
from proyectos.models import Proyecto
from usuarios.models import PerfilUsuario

from .models import Notificacion
from .services import notificar_usuario_creado


class NotificacionesTests(TestCase):
    def crear_usuario(self, username, rol):
        usuario = User.objects.create_user(
            username=username,
            password="PasswordSegura123!",
        )
        perfil = usuario.perfilusuario
        perfil.rol = rol
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
        return usuario

    def setUp(self):
        self.admin = self.crear_usuario(
            "admin-notificaciones",
            PerfilUsuario.ROL_ADMINISTRADOR,
        )
        self.dueno = self.crear_usuario(
            "dueno-notificaciones",
            PerfilUsuario.ROL_DUENO,
        )
        self.ayudante = self.crear_usuario(
            "ayudante-notificaciones",
            PerfilUsuario.ROL_AYUDANTE,
        )
        self.client_api = APIClient()
        self.cliente = ClientePotencial.objects.create(
            nombre_solicitante="Cliente notificaciones",
            telefono="6140000000",
            descripcion="",
        )
        self.cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            codigo="COT-NOTIF-001",
            descripcion="Cotización de prueba",
            subtotal=Decimal("1000.00"),
            iva=Decimal("160.00"),
            total=Decimal("1160.00"),
            creado_por=self.admin,
            modificado_por=self.admin,
        )

    def test_usuario_solo_consulta_sus_notificaciones(self):
        Notificacion.objects.create(
            usuario=self.admin,
            tipo=Notificacion.TIPO_SISTEMA,
            titulo="Admin",
            mensaje="Solo admin",
        )
        Notificacion.objects.create(
            usuario=self.ayudante,
            tipo=Notificacion.TIPO_SISTEMA,
            titulo="Ayudante",
            mensaje="Solo ayudante",
        )
        self.client_api.force_authenticate(self.admin)
        response = self.client_api.get("/api/notificaciones/")
        self.assertEqual(response.status_code, 200)
        titulos = [item["titulo"] for item in response.data["results"]]
        self.assertIn("Admin", titulos)
        self.assertNotIn("Ayudante", titulos)

    def test_marcar_leida_y_marcar_todas(self):
        primera = Notificacion.objects.create(
            usuario=self.admin,
            tipo=Notificacion.TIPO_SISTEMA,
            titulo="Primera",
            mensaje="Mensaje",
        )
        Notificacion.objects.create(
            usuario=self.admin,
            tipo=Notificacion.TIPO_SISTEMA,
            titulo="Segunda",
            mensaje="Mensaje",
        )
        self.client_api.force_authenticate(self.admin)
        response = self.client_api.post(
            f"/api/notificaciones/{primera.pk}/marcar-leida/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        primera.refresh_from_db()
        self.assertTrue(primera.leida)

        response = self.client_api.post(
            "/api/notificaciones/marcar-todas-leidas/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Notificacion.objects.filter(
                usuario=self.admin,
                leida=False,
            ).exists(),
        )

    def test_asignacion_proyecto_notifica_responsable(self):
        Proyecto.objects.create(
            cliente=self.cliente,
            nombre="Proyecto asignado",
            responsable=self.ayudante,
            creado_por=self.admin,
            modificado_por=self.admin,
        )
        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.ayudante,
                tipo=Notificacion.TIPO_PROYECTO_ASIGNADO,
            ).exists(),
        )

    def test_autorizar_cotizacion_notifica_gestion(self):
        self.cotizacion.estado = Cotizacion.ESTADO_AUTORIZADA
        self.cotizacion.modificado_por = self.admin
        self.cotizacion.save(
            update_fields=["estado", "modificado_por", "fecha_actualizacion"],
        )
        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.dueno,
                tipo=Notificacion.TIPO_COTIZACION_AUTORIZADA,
            ).exists(),
        )
        self.assertFalse(
            Notificacion.objects.filter(
                usuario=self.admin,
                tipo=Notificacion.TIPO_COTIZACION_AUTORIZADA,
            ).exists(),
        )

    @override_settings(MEDIA_ROOT=None)
    def test_factura_y_pago_generan_notificaciones(self):
        self.cotizacion.estado = Cotizacion.ESTADO_AUTORIZADA
        self.cotizacion.save(update_fields=["estado", "fecha_actualizacion"])
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                factura = FacturaDocumento.objects.create(
                    cotizacion=self.cotizacion,
                    folio="FAC-NOTIF-001",
                    archivo_pdf=SimpleUploadedFile(
                        "factura.pdf",
                        b"%PDF-1.4 prueba",
                        content_type="application/pdf",
                    ),
                    importe=Decimal("500.00"),
                    fecha_emision=timezone.localdate(),
                    creado_por=self.admin,
                    modificado_por=self.admin,
                )
                self.assertTrue(
                    Notificacion.objects.filter(
                        usuario=self.dueno,
                        tipo=Notificacion.TIPO_FACTURA_CREADA,
                    ).exists(),
                )
                Pago.objects.create(
                    cotizacion=self.cotizacion,
                    factura=factura,
                    monto=Decimal("500.00"),
                    metodo_pago="TRANSFERENCIA",
                    fecha_pago=timezone.localdate(),
                    creado_por=self.admin,
                    modificado_por=self.admin,
                )
                self.assertTrue(
                    Notificacion.objects.filter(
                        usuario=self.dueno,
                        tipo=Notificacion.TIPO_PAGO_REGISTRADO,
                    ).exists(),
                )

    def test_alerta_proyecto_proximo_no_se_duplica(self):
        Proyecto.objects.create(
            cliente=self.cliente,
            nombre="Proyecto próximo",
            responsable=self.ayudante,
            fecha_fin_estimada=timezone.localdate() + timedelta(days=2),
            creado_por=self.admin,
            modificado_por=self.admin,
        )
        self.client_api.force_authenticate(self.ayudante)
        self.client_api.get("/api/notificaciones/resumen/")
        self.client_api.get("/api/notificaciones/resumen/")
        self.assertEqual(
            Notificacion.objects.filter(
                usuario=self.ayudante,
                tipo=Notificacion.TIPO_PROYECTO_PROXIMO,
            ).count(),
            1,
        )

    def test_usuario_creado_notifica_al_usuario_y_gestion(self):
        nuevo = self.crear_usuario(
            "nuevo-notificaciones",
            PerfilUsuario.ROL_AYUDANTE,
        )
        notificar_usuario_creado(nuevo, actor=self.admin)
        self.assertTrue(
            Notificacion.objects.filter(
                usuario=nuevo,
                tipo=Notificacion.TIPO_USUARIO_CREADO,
            ).exists(),
        )
        self.assertTrue(
            Notificacion.objects.filter(
                usuario=self.dueno,
                tipo=Notificacion.TIPO_USUARIO_CREADO,
            ).exists(),
        )
