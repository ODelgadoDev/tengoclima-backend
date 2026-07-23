import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0003_remove_estado_cliente"),
        ("proyectos", "0002_proyecto_activo_proyecto_creado_por_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="proyecto",
            name="cliente",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="proyectos",
                to="clientes.clientepotencial",
            ),
        ),
    ]
