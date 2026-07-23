from django.apps import AppConfig


class CobranzaConfig(AppConfig):
    name = "cobranza"

    def ready(self):
        from . import signals  # noqa: F401
