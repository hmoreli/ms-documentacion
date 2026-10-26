# ms-documentacion

Microservicio de Documentación Laboral. Tipos de documento exigidos y documentos presentados por cada funcionario.

Implementa el contrato [`contrato/openapi.yaml`](contrato/openapi.yaml) con FastAPI, SQLAlchemy 2 y Alembic sobre PostgreSQL (schema `documentacion`).

## Respecto al contrato

- Los archivos (PDF, JPG o PNG, hasta 20 MB) se guardan en el volumen `archivos` montado en `ARCHIVOS_DIR` (por defecto `/datos/archivos`), no en la base. La base guarda nombre, tipo, tamaño y SHA-256.
  - `PUT /documentos-funcionarios/{id}/archivo` (multipart, campo `archivo`) sube o reemplaza el archivo y marca el documento como presentado.
  - `GET /documentos-funcionarios/{id}/archivo` lo descarga; `DELETE` lo quita.
  - Borrar un documento de funcionario también borra su archivo.
- Los documentos de un funcionario se listan con `/documentos-funcionarios?funcionario_id=` (reemplaza a `/search?documento_identidad=`; el documento de identidad está en ms-funcionarios).
- Búsqueda por texto con `?q=` en los tipos de documento.
- **Respaldo:** el volumen `archivos` se respalda junto con la base.
- Los ids de otros servicios (funcionario) se verifican con el servicio dueño antes de guardar: 422 si no existe, 503 si no responde. Usa el client `ms-documentacion` de Keycloak (`SERVICIO_CLIENT_ID`/`SERVICIO_CLIENT_SECRET`); sin esas variables, como en las pruebas, no se verifica.

## Desarrollo

Este repo usa `rrhh-common`, que tiene que estar clonado al lado:

```
rrhh/
├── rrhh-common/
├── rrhh-plataforma/
└── ms-documentacion/
```

```bash
python -m venv .venv && . .venv/bin/activate
pip install "../rrhh-common[db]" -e ".[dev]"
pytest              # usa SQLite en memoria, no necesita la plataforma
ruff check app tests && ruff format --check app tests
```

## Levantar con la plataforma

```bash
cd ../rrhh-plataforma && docker compose up -d
cd ../ms-documentacion && docker compose up -d --build
```

Al arrancar, el contenedor aplica las migraciones (`alembic upgrade head`) en el schema `documentacion`. Queda accesible solo por Kong en `http://localhost:8000/api/documentacion/...` con un token de Keycloak. La documentación interactiva está en `/api/documentacion/docs` (también detrás del gateway).

## Migraciones

```bash
export DATABASE_URL=postgresql+psycopg://ms_documentacion:servicio-dev@localhost:5432/rrhh
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
```

## Roles

Lectura: `rrhh-operador`, `nomina-liquidador`, `consulta`. Escritura: `rrhh-operador`. `rrhh-admin` puede todo.

## CI

GitHub Actions corre ruff y pytest. Como `rrhh-common` es privado, el repo necesita el secreto **`RRHH_COMMON_TOKEN`**: un token *fine-grained* con permiso `Contents: read` sobre `hmoreli/rrhh-common`.
