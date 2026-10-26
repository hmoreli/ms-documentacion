from datetime import UTC, datetime

from fastapi import Depends, File, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse
from rrhh_common import Usuario, requiere_roles
from rrhh_common.crud import ROLES_ESCRITURA, ROLES_LECTURA, router_crud
from sqlalchemy.orm import Session

from app import almacen
from app import esquemas as e
from app import modelos as m
from app.db import obtener_sesion

leer = requiere_roles(*ROLES_LECTURA)
escribir = requiere_roles(*ROLES_ESCRITURA)

documentos_funcionarios = router_crud(
    modelo=m.DocumentoFuncionario,
    crear=e.DocumentoFuncionario,
    parche=e.DocumentoFuncionarioUpdate,
    salida=e.DocumentoFuncionarioSalida,
    prefijo="/documentos-funcionarios",
    etiqueta="Documentos de Funcionarios",
    nombre="Documento de funcionario",
    sesion=obtener_sesion,
    filtros={"funcionario_id": int, "documento_id": int, "presentado": bool},
    # DELETE también borra el archivo del volumen (abajo).
    metodos={"listar", "crear", "obtener", "actualizar"},
)


def _buscar(db: Session, id_: int) -> m.DocumentoFuncionario:
    df = db.get(m.DocumentoFuncionario, id_)
    if df is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="Documento de funcionario no encontrado"
        )
    return df


@documentos_funcionarios.delete(
    "/{id}", status_code=204, summary="Eliminar documento de funcionario (y su archivo)"
)
def eliminar(id: int, db: Session = Depends(obtener_sesion), _: Usuario = Depends(escribir)):
    df = _buscar(db, id)
    clave = df.archivo_clave
    db.delete(df)
    db.commit()
    almacen.borrar(clave)
    return Response(status_code=204)


@documentos_funcionarios.put(
    "/{id}/archivo",
    response_model=e.DocumentoFuncionarioSalida,
    summary="Subir (o reemplazar) el archivo del documento",
    description="PDF, JPG o PNG de hasta 20 MB. Marca el documento como presentado.",
)
def subir_archivo(
    id: int,
    archivo: UploadFile = File(),
    db: Session = Depends(obtener_sesion),
    _: Usuario = Depends(escribir),
):
    df = _buscar(db, id)
    if archivo.content_type not in almacen.TIPOS_PERMITIDOS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo no permitido ({archivo.content_type}); se aceptan PDF, JPG y PNG",
        )
    contenido = archivo.file.read(almacen.TAMANO_MAXIMO + 1)
    if len(contenido) > almacen.TAMANO_MAXIMO:
        raise HTTPException(413, detail="Máximo 20 MB")
    if not contenido:
        raise HTTPException(422, detail="El archivo está vacío")
    anterior = df.archivo_clave
    df.archivo_clave, df.archivo_sha256 = almacen.guardar(contenido)
    df.archivo_nombre = (archivo.filename or "archivo")[:255]
    df.archivo_tipo = archivo.content_type
    df.archivo_tamano = len(contenido)
    df.archivo_subido_en = datetime.now(UTC)
    df.presentado = True
    try:
        db.commit()
    except Exception:
        db.rollback()
        almacen.borrar(df.archivo_clave)
        raise
    almacen.borrar(anterior)
    db.refresh(df)
    return df


@documentos_funcionarios.get(
    "/{id}/archivo",
    summary="Descargar el archivo del documento",
    response_class=FileResponse,
    responses={200: {"content": {"application/pdf": {}, "image/jpeg": {}, "image/png": {}}}},
)
def bajar_archivo(id: int, db: Session = Depends(obtener_sesion), _: Usuario = Depends(leer)):
    df = _buscar(db, id)
    if not df.archivo_clave or not almacen.ruta(df.archivo_clave).exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="El documento no tiene archivo")
    return FileResponse(
        almacen.ruta(df.archivo_clave), media_type=df.archivo_tipo, filename=df.archivo_nombre
    )


@documentos_funcionarios.delete(
    "/{id}/archivo",
    response_model=e.DocumentoFuncionarioSalida,
    summary="Quitar el archivo del documento",
)
def quitar_archivo(id: int, db: Session = Depends(obtener_sesion), _: Usuario = Depends(escribir)):
    df = _buscar(db, id)
    clave = df.archivo_clave
    for campo in ("clave", "nombre", "tipo", "tamano", "sha256", "subido_en"):
        setattr(df, f"archivo_{campo}", None)
    df.presentado = False
    db.commit()
    almacen.borrar(clave)
    db.refresh(df)
    return df


routers = [
    router_crud(
        modelo=m.Documento,
        crear=e.Documento,
        parche=e.DocumentoUpdate,
        salida=e.DocumentoSalida,
        prefijo="/documentos",
        etiqueta="Documentos",
        nombre="Documento",
        sesion=obtener_sesion,
        busqueda=("descripcion",),
        metodos={"listar", "crear", "obtener", "actualizar"},
    ),
    documentos_funcionarios,
]
