import base64

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


def test_archivo_en_base64_ida_y_vuelta(cliente):
    doc = tipo_cedula(cliente)
    df = crear(
        cliente,
        "/documentos-funcionarios",
        {
            "funcionario_id": 5,
            "documento_id": doc["id"],
            "documento_identidad": "4567890",
            "fecha_vencimiento": "2030-01-01",
            "presentado": True,
            "archivo": base64.b64encode(PDF).decode(),
        },
    )
    assert base64.b64decode(df["archivo"]) == PDF


def test_archivo_que_no_es_base64(cliente):
    doc = tipo_cedula(cliente)
    r = cliente.post(
        "/documentos-funcionarios",
        json={
            "funcionario_id": 5,
            "documento_id": doc["id"],
            "documento_identidad": "1",
            "presentado": False,
            "archivo": "esto no es base64!",
        },
        headers=OPERADOR,
    )
    assert r.status_code == 422


def test_busqueda_por_documento_identidad(cliente):
    doc = tipo_cedula(cliente)
    for cedula in ("111", "111", "222"):
        crear(
            cliente,
            "/documentos-funcionarios",
            {
                "funcionario_id": 5,
                "documento_id": doc["id"],
                "documento_identidad": cedula,
                "presentado": False,
            },
        )
    r = cliente.get("/documentos-funcionarios/search?documento_identidad=111", headers=CONSULTA)
    assert len(r.json()) == 2
    r = cliente.get("/documentos-funcionarios/search?documento_identidad=999", headers=CONSULTA)
    assert r.status_code == 404


def test_marcar_como_presentado(cliente):
    doc = tipo_cedula(cliente)
    df = crear(
        cliente,
        "/documentos-funcionarios",
        {
            "funcionario_id": 5,
            "documento_id": doc["id"],
            "documento_identidad": "1",
            "presentado": False,
        },
    )
    r = cliente.patch(
        f"/documentos-funcionarios/{df['id']}", json={"presentado": True}, headers=OPERADOR
    )
    assert r.json()["presentado"] is True
    assert r.json()["documento_identidad"] == "1"


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
    assert set(rutas["/documentos-funcionarios/{id}"]) == {"patch"}
    assert set(rutas["/documentos-funcionarios/search"]) == {"get"}
