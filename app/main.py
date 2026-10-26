"""Punto de entrada: uvicorn --factory app.main:crear_app"""

import os

from fastapi import FastAPI
from rrhh_common import (
    ConfigAuth,
    ValidadorReferencias,
    VerificadorToken,
    registrar_manejadores_errores,
)

from app.rutas import routers


def crear_app(verificador: VerificadorToken | None = None) -> FastAPI:
    app = FastAPI(
        title="Microservicio de Documentación Laboral",
        version="1.0.0",
        # Detrás de Kong el servicio vive en /api/documentacion; así /docs arma bien las URLs.
        root_path=os.environ.get("ROOT_PATH", ""),
    )
    app.state.verificador = verificador or VerificadorToken(ConfigAuth.desde_entorno())
    # Verifica con los otros servicios los ids que no son de este (ver app/referencias.py).
    app.state.referencias = ValidadorReferencias.desde_entorno()
    registrar_manejadores_errores(app)
    for router in routers:
        app.include_router(router)

    @app.get("/salud", include_in_schema=False)
    def salud() -> dict[str, str]:
        return {"estado": "ok"}

    return app
