import io
import shutil
import tempfile
import zipfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from clientes.models import ClientePotencial
from cotizaciones.models import Cotizacion
from proyectos.models import Proyecto
from usuarios.models import PerfilUsuario

from .models import Evidencia


class ArchivosTrabajoTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp(prefix="tengoclima-archivos-")
        cls.override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username="admin-archivos",
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
            nombre_solicitante="Cliente archivos",
            telefono="6140000000",
        )
        self.proyecto = Proyecto.objects.create(
            cliente=self.cliente,
            nombre="Proyecto archivos",
            responsable=self.user,
        )
        self.cotizacion = Cotizacion.objects.create(
            cliente=self.cliente,
            proyecto=self.proyecto,
            codigo="COT-ARCH-001",
            descripcion="Cotización con archivos",
            estado=Cotizacion.ESTADO_AUTORIZADA,
        )

    def _archivo(self, nombre, contenido=b"contenido", mime="application/octet-stream"):
        return SimpleUploadedFile(nombre, contenido, content_type=mime)

    def _crear_archivo_cotizacion(self, nombre="referencia.pdf", tipo="REFERENCIA"):
        return self.api.post(
            "/api/evidencias/evidencias/",
            {
                "cotizacion": self.cotizacion.pk,
                "tipo": tipo,
                "archivo": self._archivo(nombre),
                "descripcion": "Archivo de prueba",
            },
            format="multipart",
        )

    def test_acepta_imagen_pdf_y_cad(self):
        casos = [
            ("foto.jpg", "image/jpeg"),
            ("plano.pdf", "application/pdf"),
            ("instalacion.dwg", "application/acad"),
        ]

        for nombre, mime in casos:
            with self.subTest(nombre=nombre):
                response = self.api.post(
                    "/api/evidencias/evidencias/",
                    {
                        "cotizacion": self.cotizacion.pk,
                        "tipo": "EVIDENCIA",
                        "archivo": self._archivo(nombre, mime=mime),
                    },
                    format="multipart",
                )
                self.assertEqual(
                    response.status_code,
                    201,
                    getattr(response, "data", None),
                )
                self.assertEqual(
                    response.data["extension"],
                    Path(nombre).suffix.lstrip("."),
                )
                self.assertTrue(response.data["url_descarga"])

    def test_acepta_campo_imagen_por_compatibilidad(self):
        response = self.api.post(
            "/api/evidencias/evidencias/",
            {
                "cotizacion": self.cotizacion.pk,
                "tipo": "EVIDENCIA",
                "imagen": self._archivo("compatibilidad.png", mime="image/png"),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            201,
            getattr(response, "data", None),
        )
        self.assertTrue(response.data["archivo"])
        self.assertTrue(response.data["imagen"])

    def test_exige_un_solo_origen_y_rechaza_extension(self):
        response = self.api.post(
            "/api/evidencias/evidencias/",
            {
                "cotizacion": self.cotizacion.pk,
                "proyecto": self.proyecto.pk,
                "tipo": "REFERENCIA",
                "archivo": self._archivo("doble.pdf"),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

        response = self.api.post(
            "/api/evidencias/evidencias/",
            {
                "cotizacion": self.cotizacion.pk,
                "tipo": "REFERENCIA",
                "archivo": self._archivo("peligroso.exe"),
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

    def test_descarga_individual(self):
        create_response = self._crear_archivo_cotizacion("manual.pdf")
        self.assertEqual(create_response.status_code, 201)

        response = self.api.get(
            f"/api/evidencias/evidencias/{create_response.data['id']}/descargar/",
        )
        self.assertEqual(response.status_code, 200)
        contenido = b"".join(response.streaming_content)
        response.close()
        self.assertEqual(contenido, b"contenido")

    def test_zip_proyecto_incluye_archivos_propios_y_cotizaciones(self):
        propio = self.api.post(
            "/api/evidencias/evidencias/",
            {
                "proyecto": self.proyecto.pk,
                "tipo": "TECNICO",
                "archivo": self._archivo("memoria.dxf"),
            },
            format="multipart",
        )
        self.assertEqual(propio.status_code, 201, getattr(propio, "data", None))

        relacionado = self._crear_archivo_cotizacion(
            "antes.jpg",
            tipo="REFERENCIA",
        )
        self.assertEqual(
            relacionado.status_code,
            201,
            getattr(relacionado, "data", None),
        )

        response = self.api.get(
            "/api/evidencias/evidencias/descargar-zip/",
            {
                "proyecto": self.proyecto.pk,
                "incluir_cotizaciones": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        contenido = b"".join(response.streaming_content)
        response.close()

        with zipfile.ZipFile(io.BytesIO(contenido)) as comprimido:
            nombres = comprimido.namelist()

        self.assertEqual(len(nombres), 2)
        self.assertTrue(any(nombre.startswith("proyecto/") for nombre in nombres))
        self.assertTrue(
            any(nombre.startswith("cotizaciones/") for nombre in nombres),
        )

    def test_soft_delete_conserva_archivo_y_hard_delete_lo_elimina(self):
        response = self._crear_archivo_cotizacion("borrable.pdf")
        self.assertEqual(response.status_code, 201)

        evidencia = Evidencia.objects.get(pk=response.data["id"])
        nombre_storage = evidencia.archivo.name
        storage = evidencia.archivo.storage
        self.assertTrue(storage.exists(nombre_storage))

        delete_response = self.api.delete(
            f"/api/evidencias/evidencias/{evidencia.pk}/",
        )
        self.assertEqual(delete_response.status_code, 204)
        self.assertTrue(storage.exists(nombre_storage))

        evidencia = Evidencia.all_objects.get(pk=evidencia.pk)
        evidencia.hard_delete()
        self.assertFalse(storage.exists(nombre_storage))
