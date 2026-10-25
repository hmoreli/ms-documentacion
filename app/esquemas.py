"""Esquemas del contrato contrato/openapi.yaml.

`archivo` viaja en base64 dentro del JSON, como dice el contrato.
"""

import base64
import binascii
from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer, WithJsonSchema

from app.modelos import TipoDocumento


def _desde_base64(valor: Any) -> Any:
    if isinstance(valor, str):
        try:
            return base64.b64decode(valor, validate=True)
        except binascii.Error as exc:
            raise ValueError("archivo debe venir codificado en base64") from exc
    return valor


# Se decodifica al validar: model_dump() entrega los bytes reales para guardar.
ArchivoEntrada = Annotated[
    bytes,
    BeforeValidator(_desde_base64),
    WithJsonSchema({"type": "string", "format": "byte"}),
]
ArchivoSalida = Annotated[
    bytes | None,
    PlainSerializer(lambda b: base64.b64encode(b).decode() if b else None, return_type=str | None),
]
Descripcion = Annotated[str, Field(min_length=1, max_length=100)]


class Documento(BaseModel):
    descripcion: Descripcion
    tipo: TipoDocumento
    tiempo_presentacion: int | None = Field(None, ge=0, description="Días para presentarlo")
    tiene_vencimiento: bool


class DocumentoUpdate(BaseModel):
    descripcion: Descripcion | None = None
    tipo: TipoDocumento | None = None
    tiempo_presentacion: int | None = Field(None, ge=0)
    tiene_vencimiento: bool | None = None


class DocumentoSalida(Documento):
    model_config = ConfigDict(from_attributes=True)
    id: int


class DocumentoFuncionario(BaseModel):
    funcionario_id: int
    documento_id: int
    documento_identidad: Annotated[str, Field(min_length=1, max_length=50)]
    fecha_vencimiento: date | None = None
    archivo: ArchivoEntrada | None = None
    presentado: bool


class DocumentoFuncionarioUpdate(BaseModel):
    funcionario_id: int | None = None
    documento_id: int | None = None
    fecha_vencimiento: date | None = None
    archivo: ArchivoEntrada | None = None
    presentado: bool | None = None


class DocumentoFuncionarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    funcionario_id: int
    documento_id: int
    documento_identidad: str
    fecha_vencimiento: date | None
    archivo: ArchivoSalida
    presentado: bool
