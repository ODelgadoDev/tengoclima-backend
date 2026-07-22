import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def rechazada_a_cancelada(apps, schema_editor):
    Cotizacion = apps.get_model("cotizaciones", "Cotizacion")
    Cotizacion.objects.filter(estado="RECHAZADA").update(estado="CANCELADA")


def cancelada_a_rechazada(apps, schema_editor):
    Cotizacion = apps.get_model("cotizaciones", "Cotizacion")
    Cotizacion.objects.filter(estado="CANCELADA").update(estado="RECHAZADA")


class Migration(migrations.Migration):
    dependencies = [
        ("cotizaciones", "0004_remove_conceptocotizacion_activo_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(rechazada_a_cancelada, cancelada_a_rechazada),
        migrations.AlterField(
            model_name="cotizacion",
            name="estado",
            field=models.CharField(
                choices=[
                    ("PENDIENTE", "Pendiente"),
                    ("AUTORIZADA", "Autorizada"),
                    ("CANCELADA", "Cancelada"),
                    ("CONVERTIDA", "Vinculada a proyecto"),
                ],
                default="PENDIENTE",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="conceptocotizacion",
            name="unidad",
            field=models.CharField(
                choices=[
                    ("PZA", "Pieza"),
                    ("ML", "Metro lineal"),
                    ("M2", "Metro cuadrado"),
                    ("SERV", "Servicio"),
                    ("PAQ", "Paquete"),
                    ("LOTE", "Lote"),
                ],
                default="PZA",
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name="ConceptoCatalogo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("activo", models.BooleanField(default=True)),
                ("eliminado", models.BooleanField(default=False)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_actualizacion", models.DateTimeField(auto_now=True)),
                ("descripcion", models.CharField(max_length=255)),
                (
                    "unidad",
                    models.CharField(
                        choices=[
                            ("PZA", "Pieza"),
                            ("ML", "Metro lineal"),
                            ("M2", "Metro cuadrado"),
                            ("SERV", "Servicio"),
                            ("PAQ", "Paquete"),
                            ("LOTE", "Lote"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "precio_unitario",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                    ),
                ),
                (
                    "creado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="conceptocatalogo_creados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modificado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="conceptocatalogo_modificados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "concepto de catálogo",
                "verbose_name_plural": "catálogo de conceptos",
                "ordering": ["descripcion", "unidad"],
            },
        ),
        migrations.AddField(
            model_name="conceptocotizacion",
            name="catalogo",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="usos",
                to="cotizaciones.conceptocatalogo",
            ),
        ),
    ]
