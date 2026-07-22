# Generated for TENGOCLIMA usuarios V2.

import django.db.models.deletion
import usuarios.models
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def crear_perfiles_faltantes(apps, schema_editor):
    User = apps.get_model("auth", "User")
    PerfilUsuario = apps.get_model("usuarios", "PerfilUsuario")

    for usuario in User.objects.all().iterator():
        PerfilUsuario.objects.get_or_create(
            usuario_id=usuario.pk,
            defaults={
                "rol": "DUENO" if usuario.is_superuser else "AYUDANTE",
                "activo": usuario.is_active,
                "requiere_cambio_contrasena": False,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("usuarios", "0003_perfilusuario_delete_clientepotencial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="foto_perfil",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=usuarios.models.ruta_foto_perfil,
            ),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="requiere_cambio_contrasena",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="fecha_actualizacion",
            field=models.DateTimeField(
                auto_now=True,
                default=timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="RegistroActividad",
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
                    "accion",
                    models.CharField(
                        choices=[
                            ("CREAR", "Creó"),
                            ("EDITAR", "Editó"),
                            ("ELIMINAR", "Envió a papelera"),
                            ("RESTAURAR", "Restauró"),
                            (
                                "ELIMINAR_DEFINITIVO",
                                "Eliminó definitivamente",
                            ),
                            ("ACTIVAR", "Activó"),
                            ("DESACTIVAR", "Desactivó"),
                            (
                                "CAMBIAR_CONTRASENA",
                                "Cambió su contraseña",
                            ),
                            (
                                "RESTABLECER_CONTRASENA",
                                "Restableció una contraseña",
                            ),
                        ],
                        max_length=30,
                    ),
                ),
                ("modelo", models.CharField(max_length=100)),
                ("modelo_etiqueta", models.CharField(max_length=100)),
                ("objeto_id", models.CharField(blank=True, max_length=64)),
                ("objeto_repr", models.CharField(max_length=255)),
                ("descripcion", models.TextField(blank=True)),
                ("cambios", models.JSONField(blank=True, default=dict)),
                ("ruta", models.CharField(blank=True, max_length=255)),
                (
                    "ip",
                    models.GenericIPAddressField(blank=True, null=True),
                ),
                ("user_agent", models.TextField(blank=True)),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="actividades",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "registro de actividad",
                "verbose_name_plural": "registros de actividad",
                "ordering": ["-fecha", "-id"],
                "indexes": [
                    models.Index(
                        fields=["usuario", "-fecha"],
                        name="actividad_usuario_fecha",
                    ),
                    models.Index(
                        fields=["modelo", "objeto_id"],
                        name="actividad_objeto",
                    ),
                ],
            },
        ),
        migrations.RunPython(
            crear_perfiles_faltantes,
            migrations.RunPython.noop,
        ),
    ]
