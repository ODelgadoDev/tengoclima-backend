# Contratos añadidos

## Catálogo

```text
GET    /api/cotizaciones/catalogo-conceptos/
GET    /api/cotizaciones/catalogo-conceptos/{id}/
POST   /api/cotizaciones/catalogo-conceptos/
PATCH  /api/cotizaciones/catalogo-conceptos/{id}/
DELETE /api/cotizaciones/catalogo-conceptos/{id}/
GET    /api/cotizaciones/catalogo-conceptos/eliminados/
POST   /api/cotizaciones/catalogo-conceptos/{id}/restaurar/
```

Campos:

```json
{
  "id": 1,
  "descripcion": "Instalación de equipo",
  "unidad": "SERV",
  "precio_unitario": "1500.00",
  "usos": 3,
  "activo": true,
  "fecha_creacion": "...",
  "fecha_actualizacion": "..."
}
```

## Estados comerciales

```text
PENDIENTE
AUTORIZADA
CANCELADA
CONVERTIDA (temporal, administrado por Proyectos)
```

El campo `estado` queda de solo lectura en el serializer de Cotización. Debe modificarse mediante las acciones dedicadas.
