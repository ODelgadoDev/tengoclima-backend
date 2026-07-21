# Resumen de API

Base local:

```text
http://127.0.0.1:8000/api
```

## Autenticación

```text
POST /auth/login/
POST /auth/refresh/
GET  /auth/perfil/
GET  /auth/usuarios/
```

## Clientes

```text
/api/clientes/clientes/
```

## Cotizaciones

```text
/api/cotizaciones/cotizaciones/
/api/cotizaciones/conceptos-cotizacion/
```

## Proyectos

```text
/api/proyectos/proyectos/
```

## Cobranza

```text
/api/cobranza/pagos/
/api/cobranza/por-cobrar/
/api/cobranza/pagados/
```

## Contabilidad

```text
/api/contabilidad/categorias-gasto/
/api/contabilidad/gastos/
```

## Evidencias

```text
/api/evidencias/evidencias/
```

## Dashboard

```text
/api/dashboard/resumen/
/api/dashboard/finanzas/
```

## Acciones de eliminación lógica

Los ViewSets compatibles incluyen:

```text
GET  /eliminados/
POST /{id}/restaurar/
```

## Documentación interactiva

```text
/api/docs/
/api/redoc/
/api/schema/
```
