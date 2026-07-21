# TENGOCLIMA — Backend

API REST del sistema administrativo de TENGOCLIMA.

## Funciones

- JWT.
- Roles y usuarios activos.
- Clientes.
- Cotizaciones y conceptos.
- Proyectos.
- Pagos y cobranza.
- Categorías y gastos.
- Evidencias.
- Dashboard.
- Auditoría.
- Soft delete.
- Búsqueda, filtros, ordenamiento y paginación.
- Swagger, ReDoc y esquema OpenAPI.
- Archivos multimedia.

## Tecnologías

- Python
- Django
- Django REST Framework
- SimpleJWT
- django-filter
- drf-spectacular
- django-cors-headers
- Pillow
- SQLite para desarrollo local

## Instalación

```powershell
git clone https://github.com/ODelgadoDev/tengoclima-backend.git
cd tengoclima-backend

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env

python manage.py migrate
python manage.py createsuperuser
python manage.py check
python manage.py runserver
```

## Variables de entorno

```env
SECRET_KEY=coloca-una-clave-local
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

No publiques el archivo `.env`.

## Direcciones locales

```text
API:     http://127.0.0.1:8000/api/
Admin:   http://127.0.0.1:8000/admin/
Swagger: http://127.0.0.1:8000/api/docs/
ReDoc:   http://127.0.0.1:8000/api/redoc/
Schema:  http://127.0.0.1:8000/api/schema/
```

## Aplicaciones

```text
usuarios
clientes
cotizaciones
proyectos
cobranza
contabilidad
evidencias
dashboard
core
```

## Validación

```powershell
python manage.py check
python manage.py showmigrations
```

## Frontend

https://github.com/ODelgadoDev/tengoclima-frontend

## Estado

Backend funcional para desarrollo local. La configuración de producción queda pendiente para otra etapa.

## Autor

Orlando Delgado

Proyecto de estadía de Desarrollo de Software Multiplataforma.
