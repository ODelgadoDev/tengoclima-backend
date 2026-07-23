# Contratos API — Libro contable

## GET `/api/contabilidad/libro/`

Respuesta paginada:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "INGRESO-1",
      "registro_id": 1,
      "tipo": "INGRESO",
      "fecha": "2026-07-20",
      "concepto": "Pago de COT-0001",
      "categoria_id": null,
      "categoria_nombre": "Ingreso por cobranza",
      "cliente_id": 1,
      "cliente_nombre": "Empresa",
      "proyecto_id": 1,
      "proyecto_nombre": "Proyecto",
      "cotizacion_id": 1,
      "cotizacion_codigo": "COT-0001",
      "factura_id": 1,
      "factura_folio": "FAC-001",
      "metodo_pago": "TRANSFERENCIA",
      "referencia": "SPEI-001",
      "proveedor": null,
      "subtotal": "500.00",
      "iva": "80.00",
      "monto": "580.00",
      "comprobante": null,
      "notas": null,
      "creado_por": "Administrador"
    }
  ],
  "resumen": {
    "ingresos": "580.00",
    "gastos": "232.00",
    "utilidad": "348.00",
    "iva_ingresos": "80.00",
    "iva_gastos": "32.00",
    "iva_neto": "48.00",
    "movimientos": 2,
    "ingresos_count": 1,
    "gastos_count": 1
  }
}
```

## GET `/api/contabilidad/libro/resumen/`

Devuelve únicamente los totales con los mismos filtros.

## GET `/api/contabilidad/libro/exportar-excel/`

Descarga un archivo `.xlsx` con seis hojas.

## GET `/api/contabilidad/libro/exportar-csv/`

Descarga todos los movimientos filtrados en UTF-8.

## Cambios en gastos

Los gastos ahora aceptan opcionalmente:

```json
{
  "proyecto": 1,
  "cotizacion": 2,
  "iva": "160.00"
}
```

`monto` representa el total y `iva` la parte de IVA incluida dentro del total.
