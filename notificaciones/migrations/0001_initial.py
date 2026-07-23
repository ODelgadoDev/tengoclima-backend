from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notificacion",
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
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("PROYECTO_ASIGNADO", "Proyecto asignado"),
                            ("COTIZACION_AUTORIZADA", "Cotización autorizada"),
                            ("COTIZACION_CANCELADA", "Cotización cancelada"),
                            ("FACTURA_CREADA", "Factura cargada"),
                            ("FACTURA_PAGADA", "Factura pagada"),
                            ("PAGO_REGISTRADO", "Pago registrado"),
                            ("PROYECTO_PROXIMO", "Proyecto próximo a vencer"),
                            ("PROYECTO_ATRASADO", "Proyecto atrasado"),
                            ("ARCHIVO_NUEVO", "Archivo nuevo"),
                            ("USUARIO_CREADO", "Usuario creado"),
                            ("USUARIO_ACTIVADO", "Usuario activado"),
                            ("USUARIO_DESACTIVADO", "Usuario desactivado"),
                            ("SISTEMA", "Sistema"),
                        ],
                        max_length=40,
                    ),
                ),
                (
                    "nivel",
                    models.CharField(
                        choices=[
                            ("INFO", "Información"),
                            ("EXITO", "Éxito"),
                            ("ADVERTENCIA", "Advertencia"),
                            ("ERROR", "Error"),
                        ],
                        default="INFO",
                        max_length=20,
                    ),
                ),
                ("titulo", models.CharField(max_length=180)),
                ("mensaje", models.TextField()),
                ("ruta", models.CharField(blank=True, max_length=255)),
                ("modelo", models.CharField(blank=True, max_length=100)),
                ("objeto_id", models.CharField(blank=True, max_length=64)),
                ("clave", models.CharField(blank=True, max_length=255)),
                ("leida", models.BooleanField(default=False)),
                ("fecha_lectura", models.DateTimeField(blank=True, null=True)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="notificaciones_generadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notificaciones",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "notificación",
                "verbose_name_plural": "notificaciones",
                "ordering": ["-fecha_creacion", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="notificacion",
            index=models.Index(
                fields=["usuario", "leida", "-fecha_creacion"],
                name="notif_user_read_date",
            ),
        ),
        migrations.AddIndex(
            model_name="notificacion",
            index=models.Index(
                fields=["tipo", "-fecha_creacion"],
                name="notif_type_date",
            ),
        ),
        migrations.AddConstraint(
            model_name="notificacion",
            constraint=models.UniqueConstraint(
                condition=models.Q(("clave", ""), _negated=True),
                fields=("usuario", "clave"),
                name="notif_user_key_unique",
            ),
        ),
    ]
