import enum
from datetime import date

from sqlalchemy import Enum, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TipoDocumento(enum.StrEnum):
    obligatoria = "obligatoria"
    opcional = "opcional"


class Documento(Base):
    """Tipo de documento que se pide a los funcionarios (cédula, certificado, etc.)."""

    __tablename__ = "documento"
    id: Mapped[int] = mapped_column(primary_key=True)
    descripcion: Mapped[str] = mapped_column(String(100), unique=True)
    tipo: Mapped[TipoDocumento] = mapped_column(Enum(TipoDocumento, name="tipo_documento"))
    tiempo_presentacion: Mapped[int | None]
    tiene_vencimiento: Mapped[bool]


class DocumentoFuncionario(Base):
    __tablename__ = "documento_funcionario"
    id: Mapped[int] = mapped_column(primary_key=True)
    funcionario_id: Mapped[int] = mapped_column(index=True)  # ms-funcionarios
    documento_id: Mapped[int] = mapped_column(ForeignKey("documento.id"))
    # Copia de la cédula del funcionario para la búsqueda del contrato.
    documento_identidad: Mapped[str] = mapped_column(String(50), index=True)
    fecha_vencimiento: Mapped[date | None]
    archivo: Mapped[bytes | None] = mapped_column(LargeBinary)
    presentado: Mapped[bool]
