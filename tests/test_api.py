from app import almacen
from tests.conftest import CONSULTA, OPERADOR

PDF = b"%PDF-1.4 contenido de prueba"


def crear(cliente, ruta, datos):
    r = cliente.post(ruta, json=datos, headers=OPERADOR)
    assert r.status_code == 201, r.text
    return r.json()


def tipo_cedula(cliente):
    return crear(
        cliente,
        "/documentos",
        {"descripcion": "Cédula de identidad", "tipo": "obligatoria", "tiene_vencimiento": True},
    )


def documento_de(cliente, funcionario_id=5):
    doc = tipo_cedula(cliente)
    return crear(
        cliente,
        "/documentos-funcionarios",
        {"funcionario_id": funcionario_id, "documento_id": doc["id"]},
    )


def subir(cliente, id_, contenido=PDF, tipo="application/pdf", nombre="cedula.pdf"):
    return cliente.put(
        f"/documentos-funcionarios/{id_}/archivo",
        files={"archivo": (nombre, contenido, tipo)},
        headers=OPERADOR,
    )


def test_alta_sin_archivo(cliente):
    df = documento_de(cliente)
    assert df["presentado"] is False
    assert df["archivo"] is None


def test_subir_y_bajar_archivo(cliente):
    df = documento_de(cliente)
    r = subir(cliente, df["id"])
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["presentado"] is True
    assert datos["archivo"]["nombre"] == "cedula.pdf"
    assert datos["archivo"]["tipo"] == "application/pdf"
    assert datos["archivo"]["tamano"] == len(PDF)

    r = cliente.get(f"/documentos-funcionarios/{df['id']}/archivo", headers=CONSULTA)
    assert r.status_code == 200
    assert r.content == PDF
    assert r.headers["content-type"] == "application/pdf"


def test_reemplazar_archivo_borra_el_anterior(cliente):
    df = documento_de(cliente)
    subir(cliente, df["id"])
    archivos = list(almacen.directorio().rglob("*"))
    subir(cliente, df["id"], b"\x89PNG foto", "image/png", "cedula.png")
    nuevos = [a for a in almacen.directorio().rglob("*") if a.is_file()]
    assert len(nuevos) == 1
    assert nuevos[0] not in archivos


def test_tipo_de_archivo_no_permitido(cliente):
    df = documento_de(cliente)
    r = subir(cliente, df["id"], b"hola", "text/plain", "nota.txt")
    assert r.status_code == 415


def test_archivo_vacio(cliente):
    df = documento_de(cliente)
    assert subir(cliente, df["id"], b"").status_code == 422


def test_archivo_demasiado_grande(cliente, monkeypatch):
    monkeypatch.setattr(almacen, "TAMANO_MAXIMO", 10)
    df = documento_de(cliente)
    assert subir(cliente, df["id"], b"x" * 11).status_code == 413


def test_quitar_archivo(cliente):
    df = documento_de(cliente)
    subir(cliente, df["id"])
    r = cliente.delete(f"/documentos-funcionarios/{df['id']}/archivo", headers=OPERADOR)
    assert r.json()["archivo"] is None
    assert r.json()["presentado"] is False
    assert not [a for a in almacen.directorio().rglob("*") if a.is_file()]
    r = cliente.get(f"/documentos-funcionarios/{df['id']}/archivo", headers=CONSULTA)
    assert r.status_code == 404


def test_eliminar_documento_borra_el_archivo(cliente):
    df = documento_de(cliente)
    subir(cliente, df["id"])
    r = cliente.delete(f"/documentos-funcionarios/{df['id']}", headers=OPERADOR)
    assert r.status_code == 204
    assert not [a for a in almacen.directorio().rglob("*") if a.is_file()]


def test_consulta_no_puede_subir(cliente):
    df = documento_de(cliente)
    r = cliente.put(
        f"/documentos-funcionarios/{df['id']}/archivo",
        files={"archivo": ("c.pdf", PDF, "application/pdf")},
        headers=CONSULTA,
    )
    assert r.status_code == 403


def test_listar_por_funcionario(cliente):
    doc = tipo_cedula(cliente)
    for funcionario_id in (5, 5, 6):
        crear(
            cliente,
            "/documentos-funcionarios",
            {"funcionario_id": funcionario_id, "documento_id": doc["id"]},
        )
    r = cliente.get("/documentos-funcionarios?funcionario_id=5", headers=CONSULTA)
    assert len(r.json()) == 2


def test_busqueda_de_documentos(cliente):
    tipo_cedula(cliente)
    crear(
        cliente,
        "/documentos",
        {
            "descripcion": "Certificado de antecedentes",
            "tipo": "opcional",
            "tiene_vencimiento": False,
        },
    )
    r = cliente.get("/documentos?q=ANTECEDENTES", headers=CONSULTA)
    assert [d["descripcion"] for d in r.json()] == ["Certificado de antecedentes"]


def test_tipo_de_documento_invalido(cliente):
    r = cliente.post(
        "/documentos",
        json={"descripcion": "X", "tipo": "a_veces", "tiene_vencimiento": False},
        headers=OPERADOR,
    )
    assert r.status_code == 422


def test_rutas_del_contrato(cliente):
    rutas = cliente.get("/openapi.json").json()["paths"]
    assert set(rutas["/documentos"]) == {"get", "post"}
    assert set(rutas["/documentos/{id}"]) == {"get", "patch"}
    assert set(rutas["/documentos-funcionarios"]) == {"get", "post"}
    assert set(rutas["/documentos-funcionarios/{id}"]) == {"get", "patch", "delete"}
    assert set(rutas["/documentos-funcionarios/{id}/archivo"]) == {"get", "put", "delete"}
