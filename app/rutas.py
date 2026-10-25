from fastapi import APIRouter, Depends, HTTPException, Query
from rrhh_common import Usuario, requiere_roles
from rrhh_common.crud import ROLES_LECTURA, router_crud
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import esquemas as e
from app import modelos as m
from app.db import obtener_sesion

busqueda = APIRouter(prefix="/documentos-funcionarios", tags=["Documentos de Funcionarios"])


# Se registra antes que el CRUD para que /search no se tome como un {id}.
@busqueda.get(
    "/search",
    response_model=list[e.DocumentoFuncionarioSalida],
    summary="Buscar documentos de funcionario por documento de identidad",
)
def buscar_por_documento_identidad(
    documento_identidad: str = Query(..., min_length=1),
    db: Session = Depends(obtener_sesion),
    _: Usuario = Depends(requiere_roles(*ROLES_LECTURA)),
):
    consulta = (
        select(m.DocumentoFuncionario)
        .filter_by(documento_identidad=documento_identidad)
        .order_by(m.DocumentoFuncionario.id)
    )
    encontrados = db.scalars(consulta).all()
    if not encontrados:
        raise HTTPException(404, detail="No hay documentos para ese documento de identidad")
    return encontrados


routers = [
    busqueda,
    router_crud(
        modelo=m.Documento,
        crear=e.Documento,
        parche=e.DocumentoUpdate,
        salida=e.DocumentoSalida,
        prefijo="/documentos",
        etiqueta="Documentos",
        nombre="Documento",
        sesion=obtener_sesion,
        metodos={"listar", "crear", "obtener", "actualizar"},
    ),
    router_crud(
        modelo=m.DocumentoFuncionario,
        crear=e.DocumentoFuncionario,
        parche=e.DocumentoFuncionarioUpdate,
        salida=e.DocumentoFuncionarioSalida,
        prefijo="/documentos-funcionarios",
        etiqueta="Documentos de Funcionarios",
        nombre="Documento de funcionario",
        sesion=obtener_sesion,
        filtros={"funcionario_id": int, "documento_id": int},
        metodos={"listar", "crear", "actualizar"},
    ),
]
