from django.db.models import Sum

from .models import FacturaDocumento


def sincronizar_estado_factura(factura_id):
    """Mantiene el estado de la factura alineado con sus pagos activos."""
    if not factura_id:
        return None

    factura = (
        FacturaDocumento.all_objects
        .filter(pk=factura_id)
        .first()
    )
    if factura is None or factura.eliminado:
        return None

    if factura.estado == FacturaDocumento.ESTADO_CANCELADA:
        return factura

    resumen = factura.pagos.aggregate(total=Sum("monto"))
    total_pagado = resumen["total"] or 0

    if total_pagado >= factura.importe:
        ultimo_pago = factura.pagos.order_by("-fecha_pago", "-id").first()
        nuevo_estado = FacturaDocumento.ESTADO_PAGADA
        nueva_fecha = ultimo_pago.fecha_pago if ultimo_pago else factura.fecha_pago
    else:
        nuevo_estado = FacturaDocumento.ESTADO_PENDIENTE
        nueva_fecha = None

    campos = []
    if factura.estado != nuevo_estado:
        factura.estado = nuevo_estado
        campos.append("estado")
    if factura.fecha_pago != nueva_fecha:
        factura.fecha_pago = nueva_fecha
        campos.append("fecha_pago")

    if campos:
        campos.append("fecha_actualizacion")
        factura.save(update_fields=campos)

    return factura
