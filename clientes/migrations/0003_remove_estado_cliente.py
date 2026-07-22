from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0002_clientepotencial_activo_clientepotencial_creado_por_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="clientepotencial",
            name="estado",
        ),
    ]
