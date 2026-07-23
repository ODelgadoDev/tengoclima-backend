from decimal import Decimal

from django.db import transaction
from django.http import FileResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.viewsets import BaseModelViewSet
from cotizaciones.models import Cotizacion
from usuarios.models import RegistroActividad
from usuarios.permissions import EsLecturaOAdministrador, EsUsuarioActivo
from usuarios.services import capturar_campos

from .models import FacturaDocumento, Pago
from .serializers import (
    FacturaCancelarSerializer,
    FacturaDocumentoDetalleSerializer,
    FacturaDocumentoSerializer,
    FacturaMarcarPagadaSerializer,
    PagoDetalleSerializer,
    PagoSerializer,
)
from .services import sincronizar_estado_factura


def total_facturado_sin_factura(cotizacion, factura_id=None):
    facturas = FacturaDocumento.objects.filter(
        cotizacion=cotizacion,
    ).exclude(estado=FacturaDocumento.ESTADO_CANCELADA)
    if factura_id is not None:
        facturas = facturas.exclude(pk=factura_id)

    return sum(
        (factura.importe for factura in facturas),
        Decimal("0.00"),
    )


class FacturaDocumentoViewSet(BaseModelViewSet):
    queryset = (
        FacturaDocumento.objects
        .select_related(
            "cotizacion",
            "cotizacion__cliente",
            "cotizacion__proyecto",
        )
        .prefetch_related("pagos")
        .order_by("-fecha_emision", "-fecha_creacion")
    )
    serializer_class = FacturaDocumentoSerializer
    permission_classes = [EsLecturaOAdministrador]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    search_fields = [
        "folio",
        "observaciones",
        "cotizacion__codigo",
        "cotizacion__descripcion",
        "cotizacion__cliente__nombre_solicitante",
        "cotizacion__cliente__empresa",
        "cotizacion__proyecto__nombre",
    ]
    filterset_fields = [
        "cotizacion",
        "estado",
        "fecha_emision",
        "fecha_pago",
    ]
    ordering_fields = [
        "folio",
        "importe",
        "fecha_emision",
        "estado",
        "fecha_pago",
        "fecha_creacion",
        "fecha_actualizacion",
    ]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FacturaDocumentoDetalleSerializer
        return FacturaDocumentoSerializer

    def get_queryset(self):
        queryset = (
            super().get_queryset()
            .select_related(
                "cotizacion",
                "cotizacion__cliente",
                "cotizacion__proyecto",
            )
            .prefetch_related("pagos")
        )
        proyecto = self.request.query_params.get("proyecto")
        if proyecto:
            queryset = queryset.filter(cotizacion__proyecto_id=proyecto)
        return queryset

    def _bloquear_cotizacion(self, cotizacion_id):
        return (
            Cotizacion.all_objects
            .select_for_update()
            .select_related("cliente", "proyecto")
            .get(pk=cotizacion_id)
        )

    def _validar_capacidad(self, cotizacion, importe, factura_id=None):
        if cotizacion.eliminado or not cotizacion.activo:
            raise ValidationError(
                {"cotizacion": "La cotización seleccionada no está activa."},
            )
        if cotizacion.estado != Cotizacion.ESTADO_AUTORIZADA:
            raise ValidationError(
                {
                    "cotizacion": (
                        "Solo se pueden cargar facturas a cotizaciones "
                        "autorizadas."
                    ),
                },
            )
        if cotizacion.total <= 0:
            raise ValidationError(
                {"cotizacion": "La cotización no tiene un total facturable."},
            )

        total_otros = total_facturado_sin_factura(
            cotizacion,
            factura_id=factura_id,
        )
        if total_otros + importe > cotizacion.total:
            raise ValidationError(
                {
                    "importe": (
                        "La suma de facturas activas no puede superar el "
                        "total de la cotización."
                    ),
                },
            )

    @transaction.atomic
    def perform_create(self, serializer):
        cotizacion_validada = serializer.validated_data["cotizacion"]
        cotizacion = self._bloquear_cotizacion(cotizacion_validada.pk)
        importe = serializer.validated_data["importe"]
        self._validar_capacidad(cotizacion, importe)

        serializer.save(
            cotizacion=cotizacion,
            creado_por=self.request.user,
            modificado_por=self.request.user,
        )

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.instance
        cotizacion = self._bloquear_cotizacion(instance.cotizacion_id)
        importe = serializer.validated_data.get("importe", instance.importe)
        self._validar_capacidad(
            cotizacion,
            importe,
            factura_id=instance.pk,
        )
        factura = serializer.save(
            cotizacion=cotizacion,
            modificado_por=self.request.user,
        )
        sincronizar_estado_factura(factura.pk)

    def perform_destroy(self, instance):
        if Pago.all_objects.filter(factura=instance).exists():
            raise ValidationError(
                {
                    "factura": (
                        "No puedes enviar a la papelera una factura con "
                        "historial de pagos. Conserva la factura o reasigna "
                        "primero esos pagos."
                    ),
                },
            )
        super().perform_destroy(instance)

    @action(detail=True, methods=["get"], url_path="descargar")
    def descargar(self, request, pk=None):
        factura = self.get_object()
        archivo = factura.archivo_pdf
        if not archivo or not archivo.name:
            return Response(
                {"detail": "La factura no tiene un PDF disponible."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return FileResponse(
            archivo.open("rb"),
            as_attachment=True,
            filename=f"{factura.folio}.pdf",
            content_type="application/pdf",
        )

    @action(detail=True, methods=["post"], url_path="marcar-pagada")
    @transaction.atomic
    def marcar_pagada(self, request, pk=None):
        factura = (
            FacturaDocumento.all_objects
            .select_for_update()
            .select_related("cotizacion", "cotizacion__cliente")
            .get(pk=self.get_object().pk)
        )

        if factura.estado == FacturaDocumento.ESTADO_CANCELADA:
            raise ValidationError(
                {"factura": "Una factura cancelada no puede marcarse pagada."},
            )

        if factura.estado == FacturaDocumento.ESTADO_PAGADA:
            return Response(
                {
                    "success": True,
                    "message": "La factura ya está pagada.",
                    "factura": FacturaDocumentoSerializer(
                        factura,
                        context=self.get_serializer_context(),
                    ).data,
                },
                status=status.HTTP_200_OK,
            )

        payload = FacturaMarcarPagadaSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        datos = payload.validated_data

        cotizacion = self._bloquear_cotizacion(factura.cotizacion_id)
        if cotizacion.eliminado or not cotizacion.activo:
            raise ValidationError(
                {"cotizacion": "La cotización de la factura no está activa."},
            )

        pago_existente = datos.get("pago_existente")
        pago_bloqueado = None
        monto_existente = Decimal("0.00")

        if pago_existente is not None:
            pago_bloqueado = (
                Pago.all_objects
                .select_for_update()
                .get(pk=pago_existente.pk)
            )
            if pago_bloqueado.eliminado or not pago_bloqueado.activo:
                raise ValidationError(
                    {"pago_existente": "El pago seleccionado no está activo."},
                )
            if pago_bloqueado.cotizacion_id != factura.cotizacion_id:
                raise ValidationError(
                    {
                        "pago_existente": (
                            "El pago seleccionado pertenece a otra cotización."
                        ),
                    },
                )
            if (
                pago_bloqueado.factura_id is not None
                and pago_bloqueado.factura_id != factura.pk
            ):
                raise ValidationError(
                    {
                        "pago_existente": (
                            "El pago seleccionado ya pertenece a otra factura."
                        ),
                    },
                )
            if pago_bloqueado.factura_id is None:
                monto_existente = pago_bloqueado.monto

        pagado_actual = factura.monto_pagado
        disponible_factura = factura.importe - pagado_actual
        if monto_existente > disponible_factura:
            raise ValidationError(
                {
                    "pago_existente": (
                        "El pago seleccionado supera el saldo de la factura."
                    ),
                },
            )

        faltante = max(
            factura.importe - pagado_actual - monto_existente,
            Decimal("0.00"),
        )
        if faltante > cotizacion.saldo_pendiente:
            raise ValidationError(
                {
                    "factura": (
                        "La cotización ya tiene pagos no vinculados y no "
                        "dispone de saldo suficiente para crear otro pago. "
                        "Selecciona un pago existente de esta cotización."
                    ),
                },
            )

        if pago_bloqueado is not None and pago_bloqueado.factura_id is None:
            pago_bloqueado.factura = factura
            pago_bloqueado.modificado_por = request.user
            pago_bloqueado.save(
                update_fields=[
                    "factura",
                    "modificado_por",
                    "fecha_actualizacion",
                ],
            )
            self.registrar_actividad(
                RegistroActividad.ACCION_EDITAR,
                pago_bloqueado,
                cambios={
                    "factura": {
                        "antes": None,
                        "despues": factura.pk,
                    },
                },
                descripcion=(
                    f"Pago vinculado a la factura {factura.folio}."
                ),
            )

        pago_creado = None
        if faltante > 0:
            pago_creado = Pago.objects.create(
                cotizacion=cotizacion,
                factura=factura,
                monto=faltante,
                metodo_pago=datos["metodo_pago"],
                referencia=datos.get("referencia") or None,
                notas=datos.get("notas") or (
                    f"Pago generado al marcar la factura {factura.folio} "
                    "como pagada."
                ),
                fecha_pago=datos["fecha_pago"],
                creado_por=request.user,
                modificado_por=request.user,
            )
            cambios_pago = {
                campo: {"antes": None, "despues": valor}
                for campo, valor in capturar_campos(pago_creado).items()
            }
            self.registrar_actividad(
                RegistroActividad.ACCION_CREAR,
                pago_creado,
                cambios=cambios_pago,
            )

        estado_anterior = factura.estado
        factura.refresh_from_db()
        factura.estado = FacturaDocumento.ESTADO_PAGADA
        factura.fecha_pago = datos["fecha_pago"]
        factura.modificado_por = request.user
        factura.save(
            update_fields=[
                "estado",
                "fecha_pago",
                "modificado_por",
                "fecha_actualizacion",
            ],
        )
        self.registrar_actividad(
            RegistroActividad.ACCION_EDITAR,
            factura,
            cambios={
                "estado": {
                    "antes": estado_anterior,
                    "despues": FacturaDocumento.ESTADO_PAGADA,
                },
                "fecha_pago": {
                    "antes": None,
                    "despues": datos["fecha_pago"].isoformat(),
                },
            },
            descripcion=f"Factura {factura.folio} marcada como pagada.",
        )

        return Response(
            {
                "success": True,
                "message": "Factura marcada como pagada correctamente.",
                "factura": FacturaDocumentoSerializer(
                    factura,
                    context=self.get_serializer_context(),
                ).data,
                "pago_creado": (
                    PagoSerializer(pago_creado).data
                    if pago_creado is not None
                    else None
                ),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="cancelar")
    @transaction.atomic
    def cancelar(self, request, pk=None):
        factura = (
            FacturaDocumento.all_objects
            .select_for_update()
            .get(pk=self.get_object().pk)
        )
        payload = FacturaCancelarSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        if factura.estado == FacturaDocumento.ESTADO_CANCELADA:
            return Response(
                {
                    "success": True,
                    "message": "La factura ya está cancelada.",
                    "factura": FacturaDocumentoSerializer(factura).data,
                },
            )
        if factura.pagos.exists():
            raise ValidationError(
                {
                    "factura": (
                        "No puedes cancelar una factura con pagos activos. "
                        "Elimina o reasigna primero sus pagos."
                    ),
                },
            )

        estado_anterior = factura.estado
        motivo = payload.validated_data.get("motivo", "").strip()
        if motivo:
            nota = f"Cancelación: {motivo}"
            factura.observaciones = "\n".join(
                parte
                for parte in [factura.observaciones, nota]
                if parte
            )

        factura.estado = FacturaDocumento.ESTADO_CANCELADA
        factura.fecha_pago = None
        factura.modificado_por = request.user
        factura.save(
            update_fields=[
                "estado",
                "fecha_pago",
                "observaciones",
                "modificado_por",
                "fecha_actualizacion",
            ],
        )
        self.registrar_actividad(
            RegistroActividad.ACCION_EDITAR,
            factura,
            cambios={
                "estado": {
                    "antes": estado_anterior,
                    "despues": FacturaDocumento.ESTADO_CANCELADA,
                },
            },
            descripcion=f"Factura {factura.folio} cancelada.",
        )

        return Response(
            {
                "success": True,
                "message": "Factura cancelada correctamente.",
                "factura": FacturaDocumentoSerializer(factura).data,
            },
        )

    @action(detail=True, methods=["post"], url_path="reabrir")
    @transaction.atomic
    def reabrir(self, request, pk=None):
        factura = (
            FacturaDocumento.all_objects
            .select_for_update()
            .select_related("cotizacion")
            .get(pk=self.get_object().pk)
        )
        if factura.estado != FacturaDocumento.ESTADO_CANCELADA:
            raise ValidationError(
                {"factura": "Solo una factura cancelada puede reabrirse."},
            )

        cotizacion = self._bloquear_cotizacion(factura.cotizacion_id)
        self._validar_capacidad(
            cotizacion,
            factura.importe,
            factura_id=factura.pk,
        )

        factura.estado = FacturaDocumento.ESTADO_PENDIENTE
        factura.fecha_pago = None
        factura.modificado_por = request.user
        factura.save(
            update_fields=[
                "estado",
                "fecha_pago",
                "modificado_por",
                "fecha_actualizacion",
            ],
        )
        self.registrar_actividad(
            RegistroActividad.ACCION_EDITAR,
            factura,
            cambios={
                "estado": {
                    "antes": FacturaDocumento.ESTADO_CANCELADA,
                    "despues": FacturaDocumento.ESTADO_PENDIENTE,
                },
            },
            descripcion=f"Factura {factura.folio} reabierta.",
        )

        return Response(
            {
                "success": True,
                "message": "Factura reabierta correctamente.",
                "factura": FacturaDocumentoSerializer(factura).data,
            },
        )

    @action(detail=True, methods=["post"], url_path="restaurar")
    @transaction.atomic
    def restaurar(self, request, pk=None):
        factura = (
            FacturaDocumento.all_objects
            .select_for_update()
            .select_related("cotizacion")
            .get(pk=self.get_object().pk)
        )
        if not factura.eliminado:
            raise ValidationError(
                {"factura": "La factura no está en la papelera."},
            )

        cotizacion = self._bloquear_cotizacion(factura.cotizacion_id)
        if factura.estado != FacturaDocumento.ESTADO_CANCELADA:
            self._validar_capacidad(
                cotizacion,
                factura.importe,
                factura_id=factura.pk,
            )

        factura.eliminado = False
        factura.activo = True
        factura.modificado_por = request.user
        factura.save(
            update_fields=[
                "eliminado",
                "activo",
                "modificado_por",
                "fecha_actualizacion",
            ],
        )
        self.registrar_actividad(
            RegistroActividad.ACCION_RESTAURAR,
            factura,
        )

        return Response(
            {
                "success": True,
                "message": "Factura restaurada correctamente.",
                "factura": FacturaDocumentoSerializer(factura).data,
            },
        )


class PagoViewSet(BaseModelViewSet):
    queryset = (
        Pago.objects
        .select_related(
            "cotizacion",
            "cotizacion__cliente",
            "factura",
        )
        .order_by("-fecha_pago", "-fecha_creacion")
    )
    serializer_class = PagoSerializer
    permission_classes = [EsLecturaOAdministrador]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PagoDetalleSerializer
        return PagoSerializer

    search_fields = [
        "referencia",
        "notas",
        "factura__folio",
        "cotizacion__codigo",
        "cotizacion__descripcion",
        "cotizacion__cliente__nombre_solicitante",
        "cotizacion__cliente__empresa",
    ]
    filterset_fields = [
        "cotizacion",
        "factura",
        "metodo_pago",
        "fecha_pago",
    ]
    ordering_fields = [
        "monto",
        "metodo_pago",
        "fecha_pago",
        "fecha_creacion",
    ]

    @transaction.atomic
    def perform_create(self, serializer):
        cotizacion_validada = serializer.validated_data["cotizacion"]
        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .get(pk=cotizacion_validada.pk)
        )
        monto = serializer.validated_data["monto"]

        if cotizacion.eliminado or not cotizacion.activo:
            raise ValidationError(
                {"cotizacion": "La cotización seleccionada no está activa."},
            )
        if cotizacion.estado == Cotizacion.ESTADO_CANCELADA:
            raise ValidationError(
                {"cotizacion": "La cotización está cancelada."},
            )
        if cotizacion.total <= 0:
            raise ValidationError(
                {"cotizacion": "La cotización no tiene total."},
            )
        if monto > cotizacion.saldo_pendiente:
            raise ValidationError(
                {
                    "monto": (
                        "El pago no puede ser mayor al saldo pendiente "
                        "de la cotización."
                    ),
                },
            )

        factura = serializer.validated_data.get("factura")
        if factura is not None:
            factura = (
                FacturaDocumento.all_objects
                .select_for_update()
                .get(pk=factura.pk)
            )
            if factura.cotizacion_id != cotizacion.pk:
                raise ValidationError(
                    {"factura": "La factura pertenece a otra cotización."},
                )
            if factura.estado == FacturaDocumento.ESTADO_CANCELADA:
                raise ValidationError(
                    {"factura": "La factura está cancelada."},
                )
            if monto > factura.saldo_pendiente:
                raise ValidationError(
                    {
                        "monto": (
                            "El pago no puede superar el saldo pendiente "
                            "de la factura."
                        ),
                    },
                )

        serializer.save(
            cotizacion=cotizacion,
            factura=factura,
            creado_por=self.request.user,
            modificado_por=self.request.user,
        )

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.instance
        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .get(pk=instance.cotizacion_id)
        )
        monto = serializer.validated_data.get("monto", instance.monto)
        disponible = cotizacion.saldo_pendiente + instance.monto

        if monto > disponible:
            raise ValidationError(
                {
                    "monto": (
                        "El pago no puede ser mayor al saldo disponible "
                        "de la cotización."
                    ),
                },
            )

        factura = serializer.validated_data.get("factura", instance.factura)
        if factura is not None:
            factura = (
                FacturaDocumento.all_objects
                .select_for_update()
                .get(pk=factura.pk)
            )
            disponible_factura = factura.saldo_pendiente
            if instance.factura_id == factura.pk:
                disponible_factura += instance.monto
            if monto > disponible_factura:
                raise ValidationError(
                    {
                        "monto": (
                            "El pago no puede superar el saldo disponible "
                            "de la factura."
                        ),
                    },
                )

        serializer.save(
            cotizacion=cotizacion,
            factura=factura,
            modificado_por=self.request.user,
        )

    @action(detail=True, methods=["post"], url_path="restaurar")
    @transaction.atomic
    def restaurar(self, request, pk=None):
        instance = self.get_object()

        if not instance.eliminado:
            return Response(
                {
                    "success": False,
                    "message": "El registro no está eliminado.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cotizacion = (
            Cotizacion.all_objects
            .select_for_update()
            .get(pk=instance.cotizacion_id)
        )
        if cotizacion.eliminado or not cotizacion.activo:
            raise ValidationError(
                {
                    "cotizacion": (
                        "No se puede restaurar el pago porque su cotización "
                        "no está activa."
                    ),
                },
            )
        if instance.monto > cotizacion.saldo_pendiente:
            raise ValidationError(
                {
                    "monto": (
                        "No se puede restaurar el pago porque supera el "
                        "saldo pendiente actual."
                    ),
                },
            )

        if instance.factura_id:
            factura = (
                FacturaDocumento.all_objects
                .select_for_update()
                .get(pk=instance.factura_id)
            )
            if factura.eliminado or not factura.activo:
                raise ValidationError(
                    {"factura": "La factura vinculada no está activa."},
                )
            if factura.estado == FacturaDocumento.ESTADO_CANCELADA:
                raise ValidationError(
                    {"factura": "La factura vinculada está cancelada."},
                )
            if instance.monto > factura.saldo_pendiente:
                raise ValidationError(
                    {
                        "monto": (
                            "No se puede restaurar el pago porque supera "
                            "el saldo pendiente de la factura."
                        ),
                    },
                )

        instance.eliminado = False
        instance.activo = True
        instance.modificado_por = request.user
        instance.save(
            update_fields=[
                "eliminado",
                "activo",
                "modificado_por",
                "fecha_actualizacion",
            ],
        )
        self.registrar_actividad(
            RegistroActividad.ACCION_RESTAURAR,
            instance,
        )

        return Response(
            {
                "success": True,
                "message": "Registro restaurado correctamente.",
            },
            status=status.HTTP_200_OK,
        )


class PorCobrarView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        data = []
        cotizaciones = (
            Cotizacion.objects
            .select_related("cliente", "proyecto")
            .prefetch_related("pagos", "facturas")
            .order_by("-fecha_creacion")
        )

        for cotizacion in cotizaciones:
            if cotizacion.saldo_pendiente > 0:
                data.append(
                    {
                        "id": cotizacion.id,
                        "codigo": cotizacion.codigo,
                        "cliente": cotizacion.cliente.nombre_solicitante,
                        "empresa": cotizacion.cliente.empresa,
                        "proyecto": cotizacion.proyecto_id,
                        "proyecto_nombre": (
                            cotizacion.proyecto.nombre
                            if cotizacion.proyecto
                            else None
                        ),
                        "total": cotizacion.total,
                        "facturado": cotizacion.total_facturado,
                        "pendiente_facturar": cotizacion.saldo_por_facturar,
                        "estado_facturacion": cotizacion.estado_facturacion,
                        "pagado": cotizacion.total_pagado,
                        "pendiente": cotizacion.saldo_pendiente,
                        "estado": cotizacion.estado_cobranza,
                        "facturas_count": cotizacion.facturas_count,
                    },
                )

        return Response(data)


class PagadosView(APIView):
    permission_classes = [EsUsuarioActivo]

    def get(self, request):
        data = []
        cotizaciones = (
            Cotizacion.objects
            .select_related("cliente", "proyecto")
            .prefetch_related("pagos", "facturas")
            .order_by("-fecha_creacion")
        )

        for cotizacion in cotizaciones:
            if cotizacion.estado_cobranza == "PAGADO":
                data.append(
                    {
                        "id": cotizacion.id,
                        "codigo": cotizacion.codigo,
                        "cliente": cotizacion.cliente.nombre_solicitante,
                        "empresa": cotizacion.cliente.empresa,
                        "proyecto": cotizacion.proyecto_id,
                        "proyecto_nombre": (
                            cotizacion.proyecto.nombre
                            if cotizacion.proyecto
                            else None
                        ),
                        "total": cotizacion.total,
                        "facturado": cotizacion.total_facturado,
                        "estado_facturacion": cotizacion.estado_facturacion,
                        "pagado": cotizacion.total_pagado,
                        "facturas_count": cotizacion.facturas_count,
                    },
                )

        return Response(data)
