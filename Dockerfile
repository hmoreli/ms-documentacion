FROM python:3.12.7-slim

WORKDIR /srv
# rrhh-common llega como contexto adicional (ver docker-compose.yml).
COPY --from=rrhh-common . /tmp/rrhh-common
RUN pip install --no-cache-dir "/tmp/rrhh-common[db]"

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .
COPY alembic.ini ./
COPY alembic ./alembic

RUN useradd --system servicio
USER servicio
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn --factory app.main:crear_app --host 0.0.0.0 --port 8000"]
