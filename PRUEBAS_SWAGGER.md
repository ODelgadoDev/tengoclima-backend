# Pruebas Swagger — Paquete 12A

## 1. Registrar gasto relacionado

`POST /api/contabilidad/gastos/`

```json
{
  "categoria": 1,
  "proyecto": 1,
  "cotizacion": 1,
  "concepto": "Material para instalación",
  "proveedor": "Proveedor local",
  "monto": "1160.00",
  "iva": "160.00",
  "metodo_pago": "TRANSFERENCIA",
  "fecha_gasto": "2026-07-22",
  "notas": "Gasto relacionado con el proyecto"
}
```

## 2. Consultar libro

`GET /api/contabilidad/libro/?fecha_desde=2026-07-01&fecha_hasta=2026-07-31&page_size=100`

## 3. Consultar solo gastos de un proyecto

`GET /api/contabilidad/libro/?tipo=GASTO&proyecto=1&page_size=100`

## 4. Resumen

`GET /api/contabilidad/libro/resumen/?fecha_desde=2026-07-01&fecha_hasta=2026-07-31`

## 5. Excel

`GET /api/contabilidad/libro/exportar-excel/?fecha_desde=2026-07-01&fecha_hasta=2026-07-31`

## 6. CSV

`GET /api/contabilidad/libro/exportar-csv/?fecha_desde=2026-07-01&fecha_hasta=2026-07-31`
