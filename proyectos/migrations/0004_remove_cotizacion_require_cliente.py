import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cotizaciones", "0006_proyecto_multiple_y_estados"),
        ("proyectos", "0003_proyecto_cliente_nullable"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="proyecto",
            options={"ordering": ["-fecha_creacion"]},
        ),
        migrations.RemoveField(
            model_name="proyecto",
            name="cotizacion",
        ),
        migrations.AlterField(
            model_name="proyecto",
            name="cliente",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="proyectos",
                to="clientes.clientepotencial",
            ),
        ),
    ]
