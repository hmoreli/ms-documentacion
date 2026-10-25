"""Conexión a PostgreSQL. El usuario del servicio tiene search_path = su schema."""

import os
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

CONVENCION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION)


@lru_cache
def motor() -> Engine:
    return create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)


@lru_cache
def _fabrica() -> sessionmaker[Session]:
    return sessionmaker(motor(), expire_on_commit=False)


def obtener_sesion() -> Iterator[Session]:
    with _fabrica()() as sesion:
        yield sesion
