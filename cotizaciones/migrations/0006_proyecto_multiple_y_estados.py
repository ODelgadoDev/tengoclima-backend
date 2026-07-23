import django.db.models.deletion
from django.db import migrations, models


def migrar_relaciones_existentes(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    Cotizacion = apps.get_model("cotizaciones", "Cotizacion")

    for proyecto in Proyecto.objects.all().iterator():
        cotizacion_id = getattr(proyecto, "cotizacion_id", None)
        if not cotizacion_id:
            continue

        cotizacion = Cotizacion.objects.filter(pk=cotizacion_id).first()
        if cotizacion is None:
            continue

        Proyecto.objects.filter(pk=proyecto.pk).update(
            cliente_id=cotizacion.cliente_id,
        )
        Cotizacion.objects.filter(pk=cotizacion.pk).update(
            proyecto_id=proyecto.pk,
        )

    Cotizacion.objects.filter(estado="CONVERTIDA").update(
        estado="AUTORIZADA",
    )


def revertir_relaciones(apps, schema_editor):
    Proyecto = apps.get_model("proyectos", "Proyecto")
    Cotizacion = apps.get_model("cotizaciones", "Cotizacion")

    for cotizacion in Cotizacion.objects.exclude(
        proyecto_id=None,
    ).iterator():
        Proyecto.objects.filter(pk=cotizacion.proyecto_id).update(
            cotizacion_id=cotizacion.pk,
        )

    Cotizacion.objects.exclude(proyecto_id=None).update(
        estado="CONVERTIDA",
        proyecto_id=None,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("cotizaciones", "0005_catalogo_lote_y_cancelada"),
        ("proyectos", "0003_proyecto_cliente_nullable"),
    ]

    operations = [
        migrations.AddField(
            model_name="cotizacion",
            name="proyecto",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cotizaciones",
                to="proyectos.proyecto",
            ),
        ),
        migrations.RunPython(
            migrar_relaciones_existentes,
            revertir_relaciones,
        ),
        migrations.AlterField(
            model_name="cotizacion",
            name="estado",
            field=models.CharField(
                choices=[
                    ("PENDIENTE", "Pendiente"),
                    ("AUTORIZADA", "Autorizada"),
                    ("CANCELADA", "Cancelada"),
                ],
                default="PENDIENTE",
                max_length=20,
            ),
        ),
    ]
