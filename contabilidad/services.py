from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError

from cobranza.models import Pago

from .models import Gasto


CENTAVO = Decimal("0.01")
TIPOS_VALIDOS = {"INGRESO", "GASTO"}
METODOS_VALIDOS = {
    "EFECTIVO",
    "TRANSFERENCIA",
    "TARJETA",
    "CHEQUE",
    "OTRO",
}


def _decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or 0))


def _money(value):
    return _decimal(value).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _parse_positive_int(value, field):
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({field: "Debe ser un identificador válido."}) from exc
    if parsed <= 0:
        raise ValidationError({field: "Debe ser un identificador válido."})
    return parsed


def parsear_filtros(params):
    fecha_desde = parse_date(params.get("fecha_desde", ""))
    fecha_hasta = parse_date(params.get("fecha_hasta", ""))

    if params.get("fecha_desde") and fecha_desde is None:
        raise ValidationError(
            {"fecha_desde": "Usa el formato YYYY-MM-DD."},
        )
    if params.get("fecha_hasta") and fecha_hasta is None:
        raise ValidationError(
            {"fecha_hasta": "Usa el formato YYYY-MM-DD."},
        )
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise ValidationError(
            {"fecha_hasta": "Debe ser igual o posterior a fecha_desde."},
        )

    tipo = params.get("tipo", "").strip().upper() or None
    if tipo and tipo not in TIPOS_VALIDOS:
        raise ValidationError(
            {"tipo": "Usa INGRESO o GASTO."},
        )

    metodo_pago = params.get("metodo_pago", "").strip().upper() or None
    if metodo_pago and metodo_pago not in METODOS_VALIDOS:
        raise ValidationError(
            {"metodo_pago": "Método de pago no válido."},
        )

    ordering = params.get("ordering", "-fecha").strip()
    if ordering not in {"fecha", "-fecha", "monto", "-monto"}:
        raise ValidationError(
            {"ordering": "Usa fecha, -fecha, monto o -monto."},
        )

    return {
        "fecha_desde": fecha_desde,
        "fecha_hasta": fecha_hasta,
        "tipo": tipo,
        "cliente": _parse_positive_int(params.get("cliente"), "cliente"),
        "proyecto": _parse_positive_int(params.get("proyecto"), "proyecto"),
        "cotizacion": _parse_positive_int(
            params.get("cotizacion"),
            "cotizacion",
        ),
        "categoria": _parse_positive_int(
            params.get("categoria"),
            "categoria",
        ),
        "metodo_pago": metodo_pago,
        "search": params.get("search", "").strip(),
        "ordering": ordering,
    }


def _partes_pago(pago):
    cotizacion = pago.cotizacion
    total = _decimal(cotizacion.total)
    if total <= 0:
        return _money(pago.monto), Decimal("0.00")

    proporcion_subtotal = _decimal(cotizacion.subtotal) / total
    subtotal = _money(_decimal(pago.monto) * proporcion_subtotal)
    iva = _money(_decimal(pago.monto) - subtotal)
    return subtotal, iva


def _cliente_nombre(cliente):
    if cliente is None:
        return None
    return cliente.empresa or cliente.nombre_solicitante


def _movimiento_ingreso(pago):
    cotizacion = pago.cotizacion
    proyecto = cotizacion.proyecto
    cliente = cotizacion.cliente
    subtotal, iva = _partes_pago(pago)
    factura = pago.factura

    return {
        "id": f"INGRESO-{pago.id}",
        "registro_id": pago.id,
        "tipo": "INGRESO",
        "fecha": pago.fecha_pago,
        "concepto": f"Pago de {cotizacion.codigo}",
        "categoria_id": None,
        "categoria_nombre": "Ingreso por cobranza",
        "cliente_id": cliente.id,
        "cliente_nombre": _cliente_nombre(cliente),
        "proyecto_id": proyecto.id if proyecto else None,
        "proyecto_nombre": proyecto.nombre if proyecto else None,
        "cotizacion_id": cotizacion.id,
        "cotizacion_codigo": cotizacion.codigo,
        "factura_id": factura.id if factura else None,
        "factura_folio": factura.folio if factura else None,
        "metodo_pago": pago.metodo_pago,
        "referencia": pago.referencia,
        "proveedor": None,
        "subtotal": subtotal,
        "iva": iva,
        "monto": _money(pago.monto),
        "comprobante": None,
        "notas": pago.notas,
        "creado_por": (
            pago.creado_por.get_full_name()
            or pago.creado_por.username
            if pago.creado_por
            else None
        ),
    }


def _movimiento_gasto(gasto):
    cotizacion = gasto.cotizacion
    proyecto = gasto.proyecto or (cotizacion.proyecto if cotizacion else None)
    cliente = cotizacion.cliente if cotizacion else (
        proyecto.cliente if proyecto else None
    )

    return {
        "id": f"GASTO-{gasto.id}",
        "registro_id": gasto.id,
        "tipo": "GASTO",
        "fecha": gasto.fecha_gasto,
        "concepto": gasto.concepto,
        "categoria_id": gasto.categoria_id,
        "categoria_nombre": (
            gasto.categoria.nombre if gasto.categoria else "Sin categoría"
        ),
        "cliente_id": cliente.id if cliente else None,
        "cliente_nombre": _cliente_nombre(cliente),
        "proyecto_id": proyecto.id if proyecto else None,
        "proyecto_nombre": proyecto.nombre if proyecto else None,
        "cotizacion_id": cotizacion.id if cotizacion else None,
        "cotizacion_codigo": cotizacion.codigo if cotizacion else None,
        "factura_id": None,
        "factura_folio": None,
        "metodo_pago": gasto.metodo_pago,
        "referencia": None,
        "proveedor": gasto.proveedor,
        "subtotal": _money(gasto.subtotal),
        "iva": _money(gasto.iva),
        "monto": _money(gasto.monto),
        "comprobante": (
            gasto.comprobante.url if gasto.comprobante else None
        ),
        "notas": gasto.notas,
        "creado_por": (
            gasto.creado_por.get_full_name()
            or gasto.creado_por.username
            if gasto.creado_por
            else None
        ),
    }


def _filtrar_ingresos(filtros):
    queryset = (
        Pago.objects.filter(activo=True)
        .select_related(
            "cotizacion__cliente",
            "cotizacion__proyecto",
            "factura",
            "creado_por",
        )
    )

    if filtros["fecha_desde"]:
        queryset = queryset.filter(fecha_pago__gte=filtros["fecha_desde"])
    if filtros["fecha_hasta"]:
        queryset = queryset.filter(fecha_pago__lte=filtros["fecha_hasta"])
    if filtros["cliente"]:
        queryset = queryset.filter(
            cotizacion__cliente_id=filtros["cliente"],
        )
    if filtros["proyecto"]:
        queryset = queryset.filter(
            cotizacion__proyecto_id=filtros["proyecto"],
        )
    if filtros["cotizacion"]:
        queryset = queryset.filter(cotizacion_id=filtros["cotizacion"])
    if filtros["metodo_pago"]:
        queryset = queryset.filter(metodo_pago=filtros["metodo_pago"])
    if filtros["search"]:
        search = filtros["search"]
        queryset = queryset.filter(
            Q(cotizacion__codigo__icontains=search)
            | Q(cotizacion__descripcion__icontains=search)
            | Q(cotizacion__cliente__nombre_solicitante__icontains=search)
            | Q(cotizacion__cliente__empresa__icontains=search)
            | Q(cotizacion__proyecto__nombre__icontains=search)
            | Q(factura__folio__icontains=search)
            | Q(referencia__icontains=search)
            | Q(notas__icontains=search)
        )

    if filtros["categoria"]:
        return Pago.objects.none()

    return queryset


def _filtrar_gastos(filtros):
    queryset = (
        Gasto.objects.filter(activo=True)
        .select_related(
            "categoria",
            "proyecto__cliente",
            "cotizacion__cliente",
            "cotizacion__proyecto",
            "creado_por",
        )
    )

    if filtros["fecha_desde"]:
        queryset = queryset.filter(fecha_gasto__gte=filtros["fecha_desde"])
    if filtros["fecha_hasta"]:
        queryset = queryset.filter(fecha_gasto__lte=filtros["fecha_hasta"])
    if filtros["cliente"]:
        queryset = queryset.filter(
            Q(cotizacion__cliente_id=filtros["cliente"])
            | Q(proyecto__cliente_id=filtros["cliente"]),
        )
    if filtros["proyecto"]:
        queryset = queryset.filter(
            Q(proyecto_id=filtros["proyecto"])
            | Q(cotizacion__proyecto_id=filtros["proyecto"]),
        )
    if filtros["cotizacion"]:
        queryset = queryset.filter(cotizacion_id=filtros["cotizacion"])
    if filtros["categoria"]:
        queryset = queryset.filter(categoria_id=filtros["categoria"])
    if filtros["metodo_pago"]:
        queryset = queryset.filter(metodo_pago=filtros["metodo_pago"])
    if filtros["search"]:
        search = filtros["search"]
        queryset = queryset.filter(
            Q(concepto__icontains=search)
            | Q(proveedor__icontains=search)
            | Q(notas__icontains=search)
            | Q(categoria__nombre__icontains=search)
            | Q(cotizacion__codigo__icontains=search)
            | Q(cotizacion__cliente__nombre_solicitante__icontains=search)
            | Q(cotizacion__cliente__empresa__icontains=search)
            | Q(proyecto__nombre__icontains=search)
        )

    return queryset.distinct()


def obtener_movimientos(filtros):
    movimientos = []

    if filtros["tipo"] in (None, "INGRESO"):
        movimientos.extend(
            _movimiento_ingreso(pago)
            for pago in _filtrar_ingresos(filtros)
        )

    if filtros["tipo"] in (None, "GASTO"):
        movimientos.extend(
            _movimiento_gasto(gasto)
            for gasto in _filtrar_gastos(filtros)
        )

    reverse = filtros["ordering"].startswith("-")
    field = filtros["ordering"].lstrip("-")
    movimientos.sort(
        key=lambda movimiento: movimiento[field],
        reverse=reverse,
    )
    return movimientos


def resumir_movimientos(movimientos):
    ingresos = sum(
        (m["monto"] for m in movimientos if m["tipo"] == "INGRESO"),
        Decimal("0.00"),
    )
    gastos = sum(
        (m["monto"] for m in movimientos if m["tipo"] == "GASTO"),
        Decimal("0.00"),
    )
    iva_ingresos = sum(
        (m["iva"] for m in movimientos if m["tipo"] == "INGRESO"),
        Decimal("0.00"),
    )
    iva_gastos = sum(
        (m["iva"] for m in movimientos if m["tipo"] == "GASTO"),
        Decimal("0.00"),
    )

    return {
        "ingresos": _money(ingresos),
        "gastos": _money(gastos),
        "utilidad": _money(ingresos - gastos),
        "iva_ingresos": _money(iva_ingresos),
        "iva_gastos": _money(iva_gastos),
        "iva_neto": _money(iva_ingresos - iva_gastos),
        "movimientos": len(movimientos),
        "ingresos_count": sum(1 for m in movimientos if m["tipo"] == "INGRESO"),
        "gastos_count": sum(1 for m in movimientos if m["tipo"] == "GASTO"),
    }


def agrupar_movimientos(movimientos, clave_id, clave_nombre):
    grupos = defaultdict(
        lambda: {
            "id": None,
            "nombre": "Sin asignar",
            "ingresos": Decimal("0.00"),
            "gastos": Decimal("0.00"),
            "iva_ingresos": Decimal("0.00"),
            "iva_gastos": Decimal("0.00"),
            "movimientos": 0,
        },
    )

    for movimiento in movimientos:
        group_key = movimiento[clave_id] or 0
        grupo = grupos[group_key]
        grupo["id"] = movimiento[clave_id]
        grupo["nombre"] = movimiento[clave_nombre] or "Sin asignar"
        grupo["movimientos"] += 1
        if movimiento["tipo"] == "INGRESO":
            grupo["ingresos"] += movimiento["monto"]
            grupo["iva_ingresos"] += movimiento["iva"]
        else:
            grupo["gastos"] += movimiento["monto"]
            grupo["iva_gastos"] += movimiento["iva"]

    resultado = []
    for grupo in grupos.values():
        grupo["ingresos"] = _money(grupo["ingresos"])
        grupo["gastos"] = _money(grupo["gastos"])
        grupo["utilidad"] = _money(grupo["ingresos"] - grupo["gastos"])
        grupo["iva_ingresos"] = _money(grupo["iva_ingresos"])
        grupo["iva_gastos"] = _money(grupo["iva_gastos"])
        grupo["iva_neto"] = _money(
            grupo["iva_ingresos"] - grupo["iva_gastos"],
        )
        resultado.append(grupo)

    return sorted(
        resultado,
        key=lambda grupo: (grupo["nombre"] or "").lower(),
    )
