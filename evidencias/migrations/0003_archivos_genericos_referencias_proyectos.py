import mimetypes
from pathlib import Path

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q

import evidencias.models


EXTENSIONES_PERMITIDAS = [
    "dwt",
    "dwg",
    "dxf",
    "jpeg",
    "jpg",
    "pdf",
    "png",
    "webp",
]


def completar_metadatos(apps, schema_editor):
    Evidencia = apps.get_model("evidencias", "Evidencia")

    for evidencia in Evidencia.objects.all().iterator():
        nombre_guardado = evidencia.archivo.name if evidencia.archivo else ""
        nombre_original = Path(nombre_guardado).name
        extension = Path(nombre_original).suffix.lower().lstrip(".")
        mime_type = mimetypes.guess_type(nombre_original)[0] or ""
        tamanio = 0

        if evidencia.archivo:
            try:
                tamanio = evidencia.archivo.size
            except (FileNotFoundError, OSError, ValueError):
                tamanio = 0

        evidencia.tipo = "EVIDENCIA"
        evidencia.nombre_original = nombre_original[:255]
        evidencia.extension = extension[:10]
        evidencia.mime_type = mime_type[:150]
        evidencia.tamanio_bytes = max(int(tamanio or 0), 0)
        evidencia.save(
            update_fields=[
                "tipo",
                "nombre_original",
                "extension",
                "mime_type",
                "tamanio_bytes",
            ],
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("cotizaciones", "0006_proyecto_multiple_y_estados"),
        ("proyectos", "0004_remove_cotizacion_require_cliente"),
        ("evidencias", "0002_rename_fecha_subida_evidencia_fecha_creacion_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="evidencia",
            old_name="imagen",
            new_name="archivo",
        ),
        migrations.AddField(
            model_name="evidencia",
            name="extension",
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name="evidencia",
            name="mime_type",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="evidencia",
            name="nombre_original",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="evidencia",
            name="proyecto",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="archivos",
                to="proyectos.proyecto",
            ),
        ),
        migrations.AddField(
            model_name="evidencia",
            name="tamanio_bytes",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="evidencia",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("REFERENCIA", "Referencia"),
                    ("EVIDENCIA", "Evidencia"),
                    ("TECNICO", "Archivo técnico"),
                ],
                default="EVIDENCIA",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="evidencia",
            name="archivo",
            field=models.FileField(
                upload_to=evidencias.models.archivo_trabajo_upload_to,
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=EXTENSIONES_PERMITIDAS,
                    ),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="evidencia",
            name="cotizacion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="archivos",
                to="cotizaciones.cotizacion",
            ),
        ),
        migrations.RunPython(completar_metadatos, noop_reverse),
        migrations.AddConstraint(
            model_name="evidencia",
            constraint=models.CheckConstraint(
                condition=(
                    Q(cotizacion__isnull=False, proyecto__isnull=True)
                    | Q(cotizacion__isnull=True, proyecto__isnull=False)
                ),
                name="archivo_un_solo_origen",
            ),
        ),
        migrations.AddIndex(
            model_name="evidencia",
            index=models.Index(
                fields=["cotizacion", "tipo", "-fecha_creacion"],
                name="archivo_cot_tipo_fecha",
            ),
        ),
        migrations.AddIndex(
            model_name="evidencia",
            index=models.Index(
                fields=["proyecto", "tipo", "-fecha_creacion"],
                name="archivo_proy_tipo_fecha",
            ),
        ),
    ]
