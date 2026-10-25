import time
from collections.abc import Iterator

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from rrhh_common import ConfigAuth, VerificadorToken
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.modelos  # noqa: F401
from app.db import Base, obtener_sesion
from app.main import crear_app

ISSUER = "http://localhost:8080/realms/rrhh"
CLAVE = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def encabezado(*roles: str) -> dict[str, str]:
    ahora = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": "rrhh-api",
        "sub": "u-1",
        "iat": ahora,
        "exp": ahora + 300,
        "realm_access": {"roles": list(roles)},
    }
    return {"Authorization": f"Bearer {jwt.encode(claims, CLAVE, algorithm='RS256')}"}


OPERADOR = encabezado("rrhh-operador")
CONSULTA = encabezado("consulta")


@pytest.fixture
def cliente() -> Iterator[TestClient]:
    motor = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    event.listen(motor, "connect", lambda con, _: con.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(motor)
    fabrica = sessionmaker(motor, expire_on_commit=False)

    def sesion_de_prueba() -> Iterator[Session]:
        with fabrica() as s:
            yield s

    config = ConfigAuth(issuer=ISSUER, audience="rrhh-api", jwks_url="no-se-usa")
    app = crear_app(VerificadorToken(config, resolver_clave=lambda _: CLAVE.public_key()))
    app.dependency_overrides[obtener_sesion] = sesion_de_prueba
    with TestClient(app) as c:
        yield c
