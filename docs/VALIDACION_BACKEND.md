# Validación del backend

## Antes de iniciar

```powershell
.\venv\Scripts\Activate.ps1
python manage.py check
python manage.py showmigrations
```

No debe haber migraciones pendientes.

## Iniciar

```powershell
python manage.py runserver
```

## Validaciones mínimas

- Login devuelve access y refresh.
- Perfil devuelve rol y estado activo.
- Swagger carga.
- Los listados autenticados responden 200.
- Un Ayudante puede consultar.
- Un Ayudante recibe rechazo al intentar escribir.
- Evidencias aceptan `multipart/form-data`.
- Comprobantes aceptan `multipart/form-data`.
- No se permiten sobrepagos.
- Los cálculos financieros se actualizan.
- Soft delete y restauración funcionan.

## Comandos de cierre

```powershell
python manage.py check
git status
```
