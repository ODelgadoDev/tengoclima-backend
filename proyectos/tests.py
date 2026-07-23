from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from clientes.models import ClientePotencial
from cotizaciones.models import Cotizacion
from usuarios.models import PerfilUsuario

from .models import Proyecto


class ProyectosMultiplesCotizacionesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin-proyectos-v2",
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
            nombre_solicitante="Cliente proyecto",
            telefono="6140000000",
            descripcion="",
        )
        self.otro_cliente = ClientePotencial.objects.create(
            nombre_solicitante="Otro cliente",
            telefono="6140000001",
            descripcion="",
        )
        self.cotizacion_1 = Cotizacion.objects.create(
            cliente=self.cliente,
            codigo="COT-MULTI-001",
            descripcion="Primera etapa",
            estado=Cotizacion.ESTADO_AUTORIZADA,
            total=Decimal("1160.00"),
        )
        self.cotizacion_2 = Cotizacion.objects.create(
            cliente=self.cliente,
            codigo="COT-MULTI-002",
            descripcion="Segunda etapa",
            estado=Cotizacion.ESTADO_AUTORIZADA,
            total=Decimal("2320.00"),
        )
        self.cotizacion_otro_cliente = Cotizacion.objects.create(
            cliente=self.otro_cliente,
            codigo="COT-MULTI-003",
            descripcion="Cliente distinto",
            estado=Cotizacion.ESTADO_AUTORIZADA,
            total=Decimal("580.00"),
        )

    def test_crear_proyecto_manual_sin_cotizaciones(self):
        response = self.api.post(
            "/api/proyectos/proyectos/",
            {
                "cliente": self.cliente.pk,
                "nombre": "Proyecto manual",
                "responsable": self.user.pk,
                "estado": Proyecto.ESTADO_PENDIENTE,
                "notas": "Se agregarán cotizaciones después.",
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            201,
            getattr(response, "data", None),
        )
        self.assertEqual(response.data["cotizaciones_count"], 0)
        self.assertEqual(response.data["total_cotizaciones"], "0.00")

    def test_crear_proyecto_con_dos_cotizaciones(self):
        response = self.api.post(
            "/api/proyectos/proyectos/",
            {
                "cliente": self.cliente.pk,
                "nombre": "Proyecto por etapas",
                "responsable": self.user.pk,
                "estado": Proyecto.ESTADO_EN_PROCESO,
                "cotizaciones_ids": [
                    self.cotizacion_1.pk,
                    self.cotizacion_2.pk,
                ],
            },
            format="json",
        )
        self.assertEqual(
            response.status_code,
            201,
            getattr(response, "data", None),
        )
        self.cotizacion_1.refresh_from_db()
        self.cotizacion_2.refresh_from_db()
        self.assertEqual(
            self.cotizacion_1.proyecto_id,
            response.data["id"],
        )
        self.assertEqual(
            self.cotizacion_2.proyecto_id,
            response.data["id"],
        )
        self.assertEqual(response.data["cotizaciones_count"], 2)
        self.assertEqual(response.data["total_cotizaciones"], "3480.00")

    def test_agregar_y_retirar_cotizacion(self):
        proyecto = Proyecto.objects.create(
            cliente=self.cliente,
            nombre="Proyecto editable",
            responsable=self.user,
        )
        agregar = self.api.post(
            f"/api/proyectos/proyectos/{proyecto.pk}/agregar-cotizacion/",
            {"cotizacion": self.cotizacion_1.pk},
            format="json",
        )
        self.assertEqual(
            agregar.status_code,
            200,
            getattr(agregar, "data", None),
        )
        self.cotizacion_1.refresh_from_db()
        self.assertEqual(self.cotizacion_1.proyecto_id, proyecto.pk)

        retirar = self.api.post(
            f"/api/proyectos/proyectos/{proyecto.pk}/retirar-cotizacion/",
            {"cotizacion": self.cotizacion_1.pk},
            format="json",
        )
        self.assertEqual(
            retirar.status_code,
            200,
            getattr(retirar, "data", None),
        )
        self.cotizacion_1.refresh_from_db()
        self.assertIsNone(self.cotizacion_1.proyecto_id)

    def test_rechaza_cotizacion_de_otro_cliente(self):
        response = self.api.post(
            "/api/proyectos/proyectos/",
            {
                "cliente": self.cliente.pk,
                "nombre": "Proyecto inválido",
                "cotizaciones_ids": [self.cotizacion_otro_cliente.pk],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_no_permite_cancelar_cotizacion_vinculada(self):
        proyecto = Proyecto.objects.create(
            cliente=self.cliente,
            nombre="Proyecto protegido",
        )
        self.cotizacion_1.proyecto = proyecto
        self.cotizacion_1.save(update_fields=["proyecto", "fecha_actualizacion"])

        response = self.api.post(
            f"/api/cotizaciones/cotizaciones/{self.cotizacion_1.pk}/cancelar/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.cotizacion_1.refresh_from_db()
        self.assertEqual(
            self.cotizacion_1.estado,
            Cotizacion.ESTADO_AUTORIZADA,
        )
