"""Tests unitarios de la API de visitas usando mongomock (no requiere Docker/Mongo real)."""

import mongomock
import pytest
from fastapi.testclient import TestClient

from app import db


@pytest.fixture
def client(monkeypatch):
    fake_client = mongomock.MongoClient()
    fake_db = fake_client["registro_visitas_test"]

    monkeypatch.setattr(db, "_client", fake_client)
    monkeypatch.setattr(db, "_db", fake_db)
    monkeypatch.setattr(db, "connect", lambda: None)
    monkeypatch.setattr(db, "close", lambda: None)
    monkeypatch.setattr(db, "ping", lambda: True)

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def _crear_visita(client, dni="20111222333"):
    payload = {
        "nombre_visitante": "Juan Pérez",
        "dni": dni,
        "motivo": "Reunión",
        "area_visitada": "Sistemas",
        "persona_visitada": "María López",
    }
    return client.post("/visitas", json=payload)


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["mongo"] is True


def test_crear_visita(client):
    resp = _crear_visita(client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["nombre_visitante"] == "Juan Pérez"
    assert body["estado"] == "en_curso"
    assert body["fecha_hora_salida"] is None


def test_listar_visitas(client):
    _crear_visita(client, dni="1")
    _crear_visita(client, dni="2")
    resp = client.get("/visitas")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_listar_visitas_filtro_dni(client):
    _crear_visita(client, dni="111")
    _crear_visita(client, dni="222")
    resp = client.get("/visitas", params={"dni": "111"})
    assert resp.status_code == 200
    datos = resp.json()
    assert len(datos) == 1
    assert datos[0]["dni"] == "111"


def test_obtener_visita(client):
    creada = _crear_visita(client).json()
    resp = client.get(f"/visitas/{creada['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == creada["id"]


def test_obtener_visita_inexistente(client):
    resp = client.get("/visitas/000000000000000000000000")
    assert resp.status_code == 404


def test_obtener_visita_id_invalido(client):
    resp = client.get("/visitas/no-es-un-id")
    assert resp.status_code == 404


def test_registrar_salida(client):
    creada = _crear_visita(client).json()
    resp = client.patch(f"/visitas/{creada['id']}/salida")
    assert resp.status_code == 200
    body = resp.json()
    assert body["estado"] == "finalizada"
    assert body["fecha_hora_salida"] is not None


def test_registrar_salida_ya_finalizada(client):
    creada = _crear_visita(client).json()
    client.patch(f"/visitas/{creada['id']}/salida")
    resp = client.patch(f"/visitas/{creada['id']}/salida")
    assert resp.status_code == 409


def test_filtro_estado_en_curso_y_finalizada(client):
    v1 = _crear_visita(client, dni="a").json()
    _crear_visita(client, dni="b")
    client.patch(f"/visitas/{v1['id']}/salida")

    en_curso = client.get("/visitas", params={"estado": "en_curso"}).json()
    finalizadas = client.get("/visitas", params={"estado": "finalizada"}).json()

    assert len(en_curso) == 1
    assert en_curso[0]["dni"] == "b"
    assert len(finalizadas) == 1
    assert finalizadas[0]["dni"] == "a"
