import cobranza.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cobranza", "0002_pago_activo_pago_creado_por_pago_eliminado_and_more"),
        ("cotizaciones", "0006_proyecto_multiple_y_estados"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FacturaDocumento",
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
                ("folio", models.CharField(max_length=100, unique=True)),
                (
                    "archivo_pdf",
                    models.FileField(upload_to=cobranza.models.factura_upload_to),
                ),
                (
                    "importe",
                    models.DecimalField(decimal_places=2, max_digits=12),
                ),
                ("fecha_emision", models.DateField()),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("PENDIENTE", "Pendiente de pago"),
                            ("PAGADA", "Pagada"),
                            ("CANCELADA", "Cancelada"),
                        ],
                        default="PENDIENTE",
                        max_length=20,
                    ),
                ),
                ("fecha_pago", models.DateField(blank=True, null=True)),
                ("observaciones", models.TextField(blank=True, null=True)),
                (
                    "cotizacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="facturas",
                        to="cotizaciones.cotizacion",
                    ),
                ),
                (
                    "creado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_creados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "modificado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_modificados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "factura",
                "verbose_name_plural": "facturas",
                "ordering": ["-fecha_emision", "-fecha_creacion"],
            },
        ),
        migrations.AddField(
            model_name="pago",
            name="factura",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pagos",
                to="cobranza.facturadocumento",
            ),
        ),
    ]
