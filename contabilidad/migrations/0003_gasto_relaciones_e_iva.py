from decimal import Decimal

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contabilidad", "0002_gasto_activo_gasto_creado_por_gasto_eliminado_and_more"),
        ("cotizaciones", "0006_proyecto_multiple_y_estados"),
        ("proyectos", "0004_remove_cotizacion_require_cliente"),
    ]

    operations = [
        migrations.AddField(
            model_name="gasto",
            name="cotizacion",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="gastos",
                to="cotizaciones.cotizacion",
            ),
        ),
        migrations.AddField(
            model_name="gasto",
            name="iva",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                help_text="IVA incluido dentro del monto total del gasto.",
                max_digits=12,
            ),
        ),
        migrations.AddField(
            model_name="gasto",
            name="proyecto",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="gastos",
                to="proyectos.proyecto",
            ),
        ),
    ]
