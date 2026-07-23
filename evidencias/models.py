import mimetypes
from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q
from django.utils.text import slugify

from cotizaciones.models import Cotizacion
from core.models import AuditableModel
from proyectos.models import Proyecto


EXTENSIONES_IMAGEN = {"jpg", "jpeg", "png", "webp"}
EXTENSIONES_PDF = {"pdf"}
EXTENSIONES_CAD = {"dwg", "dxf", "dwt"}
EXTENSIONES_PERMITIDAS = sorted(
    EXTENSIONES_IMAGEN | EXTENSIONES_PDF | EXTENSIONES_CAD,
)
TAMANIO_MAXIMO_BYTES = 50 * 1024 * 1024


def archivo_trabajo_upload_to(instance, filename):
    """Organiza archivos por origen, tipo y nombre seguro."""
    original = Path(filename)
    extension = original.suffix.lower()
    nombre_seguro = slugify(original.stem) or "archivo"
    nombre_final = f"{nombre_seguro}-{uuid4().hex[:10]}{extension}"

    if instance.cotizacion_id:
        origen = f"cotizaciones/{instance.cotizacion_id}"
    elif instance.proyecto_id:
        origen = f"proyectos/{instance.proyecto_id}"
    else:
        origen = "sin-origen"

    tipo = (instance.tipo or Evidencia.TIPO_EVIDENCIA).lower()
    return f"archivos/{origen}/{tipo}/{nombre_final}"


class Evidencia(AuditableModel):
    TIPO_REFERENCIA = "REFERENCIA"
    TIPO_EVIDENCIA = "EVIDENCIA"
    TIPO_TECNICO = "TECNICO"

    TIPOS = [
        (TIPO_REFERENCIA, "Referencia"),
        (TIPO_EVIDENCIA, "Evidencia"),
        (TIPO_TECNICO, "Archivo técnico"),
    ]

    cotizacion = models.ForeignKey(
        Cotizacion,
        on_delete=models.CASCADE,
        related_name="archivos",
        null=True,
        blank=True,
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="archivos",
        null=True,
        blank=True,
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default=TIPO_EVIDENCIA,
    )
    archivo = models.FileField(
        upload_to=archivo_trabajo_upload_to,
        validators=[FileExtensionValidator(EXTENSIONES_PERMITIDAS)],
    )
    nombre_original = models.CharField(max_length=255, blank=True)
    extension = models.CharField(max_length=10, blank=True)
    mime_type = models.CharField(max_length=150, blank=True)
    tamanio_bytes = models.PositiveBigIntegerField(default=0)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["-fecha_creacion"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(cotizacion__isnull=False, proyecto__isnull=True)
                    | Q(cotizacion__isnull=True, proyecto__isnull=False)
                ),
                name="archivo_un_solo_origen",
            ),
        ]
        indexes = [
            models.Index(
                fields=["cotizacion", "tipo", "-fecha_creacion"],
                name="archivo_cot_tipo_fecha",
            ),
            models.Index(
                fields=["proyecto", "tipo", "-fecha_creacion"],
                name="archivo_proy_tipo_fecha",
            ),
        ]
        verbose_name = "archivo de trabajo"
        verbose_name_plural = "archivos de trabajo"

    def clean(self):
        super().clean()

        if bool(self.cotizacion_id) == bool(self.proyecto_id):
            raise ValidationError(
                "El archivo debe pertenecer a una cotización o a un "
                "proyecto, pero no a ambos.",
            )

        if self.archivo:
            extension = Path(self.archivo.name).suffix.lower().lstrip(".")
            if extension not in EXTENSIONES_PERMITIDAS:
                raise ValidationError(
                    {
                        "archivo": (
                            "Formato no permitido. Usa JPG, JPEG, PNG, WEBP, "
                            "PDF, DWG, DXF o DWT."
                        ),
                    },
                )

            try:
                tamanio = self.archivo.size
            except (OSError, ValueError):
                tamanio = 0

            if tamanio > TAMANIO_MAXIMO_BYTES:
                raise ValidationError(
                    {"archivo": "El archivo no puede superar 50 MB."},
                )

    def actualizar_metadatos(self):
        if not self.archivo:
            return

        nombre = self.nombre_original or Path(self.archivo.name).name
        extension = Path(nombre).suffix.lower().lstrip(".")
        mime_type = self.mime_type or mimetypes.guess_type(nombre)[0] or ""

        try:
            tamanio = self.archivo.size
        except (OSError, ValueError):
            tamanio = self.tamanio_bytes or 0

        self.nombre_original = Path(nombre).name[:255]
        self.extension = extension[:10]
        self.mime_type = mime_type[:150]
        self.tamanio_bytes = max(int(tamanio or 0), 0)

    def save(self, *args, **kwargs):
        self.actualizar_metadatos()
        super().save(*args, **kwargs)

    @property
    def es_imagen(self):
        return self.extension.lower() in EXTENSIONES_IMAGEN

    @property
    def es_pdf(self):
        return self.extension.lower() in EXTENSIONES_PDF

    @property
    def es_cad(self):
        return self.extension.lower() in EXTENSIONES_CAD

    @property
    def clase_archivo(self):
        if self.es_imagen:
            return "IMAGEN"
        if self.es_pdf:
            return "PDF"
        if self.es_cad:
            return "CAD"
        return "OTRO"

    @property
    def origen_descripcion(self):
        if self.cotizacion_id:
            return self.cotizacion.codigo
        if self.proyecto_id:
            return self.proyecto.nombre
        return "Sin origen"

    def __str__(self):
        return (
            f"{self.get_tipo_display()} {self.id} - "
            f"{self.origen_descripcion}"
        )
