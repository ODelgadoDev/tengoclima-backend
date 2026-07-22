from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import AuthenticationFailed

from .models import PerfilUsuario


class TokenTengoclimaSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "No fue posible iniciar sesión con las credenciales proporcionadas.",
    }

    def validate(self, attrs):
        data = super().validate(attrs)
        perfil, _ = PerfilUsuario.objects.get_or_create(
            usuario=self.user,
            defaults={
                "rol": (
                    PerfilUsuario.ROL_DUENO
                    if self.user.is_superuser
                    else PerfilUsuario.ROL_AYUDANTE
                ),
                "activo": self.user.is_active,
            },
        )

        if not perfil.activo or not self.user.is_active:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                code="no_active_account",
            )

        return data


class TokenTengoclimaView(TokenObtainPairView):
    serializer_class = TokenTengoclimaSerializer
