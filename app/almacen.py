"""Archivos de legajos en el volumen del servicio (sin MinIO).

Cada archivo se guarda con un nombre aleatorio en ARCHIVOS_DIR (por defecto
/datos/archivos, montado como volumen en docker-compose). La base guarda la clave,
el nombre original, el tipo, el tamaño y el SHA-256.
"""

import hashlib
import os
import uuid
from pathlib import Path

TAMANO_MAXIMO = 20 * 1024 * 1024
TIPOS_PERMITIDOS = {"application/pdf", "image/jpeg", "image/png"}


def directorio() -> Path:
    return Path(os.environ.get("ARCHIVOS_DIR", "/datos/archivos"))


def ruta(clave: str) -> Path:
    # Subcarpeta por los dos primeros caracteres, para no juntar miles de archivos en una.
    return directorio() / clave[:2] / clave


def guardar(contenido: bytes) -> tuple[str, str]:
    """Guarda el contenido y devuelve (clave, sha256)."""
    clave = uuid.uuid4().hex
    destino = ruta(clave)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".tmp")
    temporal.write_bytes(contenido)
    temporal.replace(destino)
    return clave, hashlib.sha256(contenido).hexdigest()


def borrar(clave: str | None) -> None:
    if clave:
        ruta(clave).unlink(missing_ok=True)
