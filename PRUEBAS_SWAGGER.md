# Pruebas Swagger — paquete 07A

## 1. Clientes sin estado

```http
POST /api/clientes/clientes/
```

```json
{
  "nombre_solicitante": "Cliente V2",
  "empresa": "Empresa de prueba",
  "telefono": "6140000000",
  "direccion": "Chihuahua",
  "descripcion": "Cliente sin proceso de autorización"
}
```

Esperado: `201` y la respuesta no contiene `estado`.

## 2. Crear concepto de catálogo

```http
POST /api/cotizaciones/catalogo-conceptos/
```

```json
{
  "descripcion": "Instalación de equipos por lote",
  "unidad": "LOTE",
  "precio_unitario": "2500.00"
}
```

Esperado: `201`.

## 3. Usar catálogo en una cotización

```http
POST /api/cotizaciones/conceptos-cotizacion/
```

```json
{
  "cotizacion": 1,
  "catalogo": 1,
  "cantidad": "2.00"
}
```

Esperado: `201`; descripción, unidad y precio se copian del catálogo. Total esperado: `5000.00`.

## 4. Autorizar

```http
POST /api/cotizaciones/cotizaciones/1/autorizar/
```

Esperado: `200`, estado `AUTORIZADA`.

## 5. Cancelar

```http
POST /api/cotizaciones/cotizaciones/1/cancelar/
```

Esperado: `200`, estado `CANCELADA`.

## 6. Reabrir

```http
POST /api/cotizaciones/cotizaciones/1/reabrir/
```

Esperado: `200`, estado `PENDIENTE`.

## 7. Dashboard

```http
GET /api/dashboard/resumen/
```

Debe incluir `cotizaciones_canceladas` en lugar de `cotizaciones_rechazadas`.
