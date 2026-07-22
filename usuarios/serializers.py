from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from .models import PerfilUsuario, RegistroActividad


def validar_email_unico(value, *, usuario_actual=None):
    email = value.strip().lower()

    queryset = User.objects.filter(email__iexact=email)
    if usuario_actual is not None:
        queryset = queryset.exclude(pk=usuario_actual.pk)

    if queryset.exists():
        raise serializers.ValidationError(
            "Ya existe un usuario con este correo electrónico.",
        )

    return email


def validar_username_unico(value, *, usuario_actual=None):
    username = value.strip()

    queryset = User.objects.filter(username__iexact=username)
    if usuario_actual is not None:
        queryset = queryset.exclude(pk=usuario_actual.pk)

    if queryset.exists():
        raise serializers.ValidationError(
            "Ya existe un usuario con este nombre de usuario.",
        )

    return username


def validar_password(password, usuario=None):
    try:
        password_validation.validate_password(password, usuario)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(
        source="usuario.id",
        read_only=True,
    )
    username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )
    first_name = serializers.CharField(
        source="usuario.first_name",
        read_only=True,
    )
    last_name = serializers.CharField(
        source="usuario.last_name",
        read_only=True,
    )
    nombre_completo = serializers.SerializerMethodField()
    email = serializers.EmailField(
        source="usuario.email",
        read_only=True,
    )

    class Meta:
        model = PerfilUsuario
        fields = [
            "id",
            "usuario_id",
            "username",
            "first_name",
            "last_name",
            "nombre_completo",
            "email",
            "rol",
            "telefono",
            "foto_perfil",
            "activo",
            "requiere_cambio_contrasena",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = fields

    def get_nombre_completo(self, obj):
        return obj.usuario.get_full_name().strip() or obj.usuario.username


class PerfilPropioSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(
        source="usuario.id",
        read_only=True,
    )
    username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )
    first_name = serializers.CharField(
        source="usuario.first_name",
        required=False,
        allow_blank=True,
        max_length=150,
    )
    last_name = serializers.CharField(
        source="usuario.last_name",
        required=False,
        allow_blank=True,
        max_length=150,
    )
    nombre_completo = serializers.SerializerMethodField()
    email = serializers.EmailField(
        source="usuario.email",
        required=False,
    )
    eliminar_foto = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
    )

    class Meta:
        model = PerfilUsuario
        fields = [
            "id",
            "usuario_id",
            "username",
            "first_name",
            "last_name",
            "nombre_completo",
            "email",
            "rol",
            "telefono",
            "foto_perfil",
            "eliminar_foto",
            "activo",
            "requiere_cambio_contrasena",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        read_only_fields = [
            "id",
            "usuario_id",
            "username",
            "nombre_completo",
            "rol",
            "activo",
            "requiere_cambio_contrasena",
            "fecha_creacion",
            "fecha_actualizacion",
        ]
        extra_kwargs = {
            "foto_perfil": {
                "required": False,
                "allow_null": True,
            },
            "telefono": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            },
        }

    def get_nombre_completo(self, obj):
        return obj.usuario.get_full_name().strip() or obj.usuario.username

    def validate_email(self, value):
        return validar_email_unico(
            value,
            usuario_actual=self.instance.usuario,
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        usuario_data = validated_data.pop("usuario", {})
        eliminar_foto = validated_data.pop("eliminar_foto", False)
        foto_nueva = validated_data.get("foto_perfil")
        foto_anterior = instance.foto_perfil
        nombre_foto_anterior = foto_anterior.name if foto_anterior else ""
        storage_anterior = foto_anterior.storage if foto_anterior else None

        usuario = instance.usuario
        for campo, valor in usuario_data.items():
            setattr(usuario, campo, valor.strip() if isinstance(valor, str) else valor)
        if usuario_data:
            usuario.save(update_fields=list(usuario_data.keys()))

        if eliminar_foto:
            validated_data["foto_perfil"] = None

        instance = super().update(instance, validated_data)

        if nombre_foto_anterior and (
            eliminar_foto
            or (
                foto_nueva is not None
                and instance.foto_perfil.name != nombre_foto_anterior
            )
        ):
            transaction.on_commit(
                lambda: storage_anterior.delete(nombre_foto_anterior),
            )

        return instance


class CambiarContrasenaSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        usuario = self.context["request"].user

        if not usuario.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "La contraseña actual no es correcta."},
            )

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Las contraseñas no coinciden."},
            )

        validar_password(attrs["new_password"], usuario)
        return attrs

    def save(self, **kwargs):
        usuario = self.context["request"].user
        usuario.set_password(self.validated_data["new_password"])
        usuario.save(update_fields=["password"])

        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=usuario)
        perfil.requiere_cambio_contrasena = False
        perfil.save(
            update_fields=[
                "requiere_cambio_contrasena",
                "fecha_actualizacion",
            ],
        )

        return usuario


class UsuarioResponsableSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source="usuario.id",
        read_only=True,
    )
    username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )
    first_name = serializers.CharField(
        source="usuario.first_name",
        read_only=True,
    )
    last_name = serializers.CharField(
        source="usuario.last_name",
        read_only=True,
    )
    email = serializers.EmailField(
        source="usuario.email",
        read_only=True,
    )
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = PerfilUsuario
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "nombre_completo",
            "email",
            "rol",
        ]

    def get_nombre_completo(self, obj):
        return obj.usuario.get_full_name().strip() or obj.usuario.username


class UsuarioAdministracionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=150,
    )
    nombre_completo = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField()
    rol = serializers.ChoiceField(choices=PerfilUsuario.ROLES)
    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=20,
    )
    foto_perfil = serializers.SerializerMethodField(read_only=True)
    activo = serializers.BooleanField(read_only=True)
    requiere_cambio_contrasena = serializers.BooleanField(read_only=True)
    fecha_creacion = serializers.DateTimeField(read_only=True)
    fecha_actualizacion = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True, allow_null=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        trim_whitespace=False,
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=False,
        trim_whitespace=False,
    )

    def get_nombre_completo(self, obj):
        return obj.get_full_name().strip() or obj.username

    def get_foto_perfil(self, obj):
        perfil = getattr(obj, "perfilusuario", None)
        if not perfil or not perfil.foto_perfil:
            return None

        request = self.context.get("request")
        url = perfil.foto_perfil.url
        return request.build_absolute_uri(url) if request else url

    def to_representation(self, instance):
        perfil = instance.perfilusuario
        return {
            "id": instance.id,
            "username": instance.username,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "nombre_completo": self.get_nombre_completo(instance),
            "email": instance.email,
            "rol": perfil.rol,
            "telefono": perfil.telefono,
            "foto_perfil": self.get_foto_perfil(instance),
            "activo": instance.is_active and perfil.activo,
            "requiere_cambio_contrasena": (
                perfil.requiere_cambio_contrasena
            ),
            "fecha_creacion": perfil.fecha_creacion,
            "fecha_actualizacion": perfil.fecha_actualizacion,
            "last_login": instance.last_login,
        }

    def validate_username(self, value):
        return validar_username_unico(
            value,
            usuario_actual=self.instance,
        )

    def validate_email(self, value):
        return validar_email_unico(
            value,
            usuario_actual=self.instance,
        )

    def validate(self, attrs):
        request = self.context["request"]
        actor = request.user
        actor_perfil = actor.perfilusuario
        instance = self.instance

        if instance is not None:
            target_perfil = instance.perfilusuario

            if (
                actor_perfil.rol == PerfilUsuario.ROL_ADMINISTRADOR
                and target_perfil.rol == PerfilUsuario.ROL_DUENO
            ):
                raise serializers.ValidationError(
                    "Un Administrador no puede modificar a un Dueño.",
                )

            nuevo_rol = attrs.get("rol", target_perfil.rol)

            if instance.pk == actor.pk and nuevo_rol != target_perfil.rol:
                raise serializers.ValidationError(
                    {"rol": "No puedes cambiar tu propio rol."},
                )

            if (
                target_perfil.rol == PerfilUsuario.ROL_DUENO
                and nuevo_rol != PerfilUsuario.ROL_DUENO
                and PerfilUsuario.objects.filter(
                    rol=PerfilUsuario.ROL_DUENO,
                    activo=True,
                    usuario__is_active=True,
                ).count() <= 1
            ):
                raise serializers.ValidationError(
                    {"rol": "No se puede cambiar el rol del último Dueño activo."},
                )

        rol = attrs.get(
            "rol",
            self.instance.perfilusuario.rol if self.instance else None,
        )

        if (
            actor_perfil.rol == PerfilUsuario.ROL_ADMINISTRADOR
            and rol == PerfilUsuario.ROL_DUENO
        ):
            raise serializers.ValidationError(
                {"rol": "Un Administrador no puede crear ni asignar el rol Dueño."},
            )

        if self.instance is None:
            password = attrs.get("password")
            password_confirm = attrs.get("password_confirm")

            if not password:
                raise serializers.ValidationError(
                    {"password": "La contraseña temporal es obligatoria."},
                )

            if password != password_confirm:
                raise serializers.ValidationError(
                    {"password_confirm": "Las contraseñas no coinciden."},
                )

            usuario_temporal = User(
                username=attrs.get("username", ""),
                email=attrs.get("email", ""),
                first_name=attrs.get("first_name", ""),
                last_name=attrs.get("last_name", ""),
            )
            validar_password(password, usuario_temporal)

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password_confirm", None)
        rol = validated_data.pop("rol")
        telefono = validated_data.pop("telefono", None)

        for campo in ("first_name", "last_name"):
            if campo in validated_data:
                validated_data[campo] = validated_data[campo].strip()

        usuario = User.objects.create_user(
            password=password,
            **validated_data,
        )
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=usuario)
        perfil.rol = rol
        perfil.telefono = telefono or None
        perfil.activo = True
        perfil.requiere_cambio_contrasena = True
        perfil.save()

        return usuario

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop("password", None)
        validated_data.pop("password_confirm", None)
        rol = validated_data.pop("rol", instance.perfilusuario.rol)
        telefono = validated_data.pop(
            "telefono",
            instance.perfilusuario.telefono,
        )

        for campo, valor in validated_data.items():
            setattr(instance, campo, valor.strip() if isinstance(valor, str) else valor)
        if validated_data:
            instance.save(update_fields=list(validated_data.keys()))

        perfil = instance.perfilusuario
        perfil.rol = rol
        perfil.telefono = telefono or None
        perfil.save(
            update_fields=[
                "rol",
                "telefono",
                "fecha_actualizacion",
            ],
        )

        return instance


class RestablecerContrasenaSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Las contraseñas no coinciden."},
            )

        validar_password(attrs["password"], self.context.get("usuario"))
        return attrs


class RegistroActividadSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(
        source="usuario.id",
        read_only=True,
        allow_null=True,
    )
    usuario_username = serializers.CharField(
        source="usuario.username",
        read_only=True,
        allow_null=True,
    )
    usuario_nombre = serializers.SerializerMethodField()
    accion_nombre = serializers.CharField(
        source="get_accion_display",
        read_only=True,
    )

    class Meta:
        model = RegistroActividad
        fields = [
            "id",
            "usuario_id",
            "usuario_username",
            "usuario_nombre",
            "accion",
            "accion_nombre",
            "modelo",
            "modelo_etiqueta",
            "objeto_id",
            "objeto_repr",
            "descripcion",
            "cambios",
            "ruta",
            "fecha",
        ]
        read_only_fields = fields

    def get_usuario_nombre(self, obj):
        if not obj.usuario:
            return "Sistema"

        return obj.usuario.get_full_name().strip() or obj.usuario.username
