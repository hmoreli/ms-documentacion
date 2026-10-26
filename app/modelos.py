import enum
from datetime import date, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
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
    """Documento presentado por un funcionario. El archivo vive en el volumen del servicio."""

    __tablename__ = "documento_funcionario"
    id: Mapped[int] = mapped_column(primary_key=True)
    funcionario_id: Mapped[int] = mapped_column(index=True)  # ms-funcionarios
    documento_id: Mapped[int] = mapped_column(ForeignKey("documento.id"))
    fecha_vencimiento: Mapped[date | None]
    presentado: Mapped[bool]
    # Datos del archivo subido (ver app/almacen.py). Todos NULL si todavía no hay archivo.
    archivo_clave: Mapped[str | None] = mapped_column(String(64), unique=True)
    archivo_nombre: Mapped[str | None] = mapped_column(String(255))
    archivo_tipo: Mapped[str | None] = mapped_column(String(100))
    archivo_tamano: Mapped[int | None]
    archivo_sha256: Mapped[str | None] = mapped_column(String(64))
    archivo_subido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def archivo(self) -> dict | None:
        """Datos del archivo para la API (None si todavía no se subió)."""
        if not self.archivo_clave:
            return None
        return {
            "nombre": self.archivo_nombre,
            "tipo": self.archivo_tipo,
            "tamano": self.archivo_tamano,
            "sha256": self.archivo_sha256,
            "subido_en": self.archivo_subido_en,
        }
