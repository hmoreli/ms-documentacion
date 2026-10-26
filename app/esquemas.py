"""Esquemas de la API (contrato en contrato/openapi.yaml, generado desde el código).

Cambios respecto al contrato original (aprobados con la revisión de contratos vs BD):
- El archivo ya no viaja en base64 dentro del JSON: se sube y se descarga aparte
  (multipart) en /documentos-funcionarios/{id}/archivo y se guarda en un volumen.
- Se quita `documento_identidad` (duplicaba la cédula de ms-funcionarios): los
  documentos de una persona se buscan con ?funcionario_id=.
"""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.modelos import TipoDocumento

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
    fecha_vencimiento: date | None = None
    presentado: bool = False


class DocumentoFuncionarioUpdate(BaseModel):
    documento_id: int | None = None
    fecha_vencimiento: date | None = None
    presentado: bool | None = None


class Archivo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    nombre: str
    tipo: str
    tamano: int = Field(description="Bytes")
    sha256: str
    subido_en: datetime


class DocumentoFuncionarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    funcionario_id: int
    documento_id: int
    fecha_vencimiento: date | None
    presentado: bool
    archivo: Archivo | None = Field(
        None, description="Datos del archivo; el contenido se baja de .../{id}/archivo"
    )
