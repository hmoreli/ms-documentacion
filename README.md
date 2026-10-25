# ms-documentacion

Microservicio de Documentación Laboral. Tipos de documento exigidos y documentos presentados por cada funcionario.

Implementa el contrato [`contrato/openapi.yaml`](contrato/openapi.yaml) con FastAPI, SQLAlchemy 2 y Alembic sobre PostgreSQL (schema `documentacion`).

## Respecto al contrato

- Respeta el contrato: `archivo` viaja en base64 dentro del JSON y se guarda en la base. Para archivos grandes conviene pasar a `multipart/form-data` y guardarlos en un volumen (pendiente de decidir).
- `GET /documentos-funcionarios/search?documento_identidad=` responde 404 si no hay resultados, como dice el contrato.
- Como en el contrato, no hay DELETE ni GET por id en documentos de funcionarios.

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
