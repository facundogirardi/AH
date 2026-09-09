"""Endpoints de negocio para el registro de visitas."""

from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query

from app.db import get_visitas_collection
from app.models import VisitaCreate, VisitaOut

router = APIRouter(prefix="/visitas", tags=["visitas"])


def _to_out(doc: dict) -> VisitaOut:
    return VisitaOut(
        id=str(doc["_id"]),
        nombre_visitante=doc["nombre_visitante"],
        dni=doc["dni"],
        motivo=doc["motivo"],
        area_visitada=doc["area_visitada"],
        persona_visitada=doc["persona_visitada"],
        fecha_hora_entrada=doc["fecha_hora_entrada"],
        fecha_hora_salida=doc.get("fecha_hora_salida"),
        estado="finalizada" if doc.get("fecha_hora_salida") else "en_curso",
    )


def _parse_object_id(visita_id: str) -> ObjectId:
    try:
        return ObjectId(visita_id)
    except InvalidId:
        raise HTTPException(status_code=404, detail="Visita no encontrada") from None


@router.post("", response_model=VisitaOut, status_code=201)
def crear_visita(visita: VisitaCreate) -> VisitaOut:
    coleccion = get_visitas_collection()
    doc = visita.model_dump()
    doc["fecha_hora_entrada"] = datetime.now(timezone.utc)
    doc["fecha_hora_salida"] = None
    resultado = coleccion.insert_one(doc)
    doc["_id"] = resultado.inserted_id
    return _to_out(doc)


@router.get("", response_model=list[VisitaOut])
def listar_visitas(
    dni: Optional[str] = None,
    estado: Optional[str] = Query(None, pattern="^(en_curso|finalizada)$"),
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> list[VisitaOut]:
    coleccion = get_visitas_collection()
    filtro: dict = {}
    if dni:
        filtro["dni"] = dni
    if estado == "finalizada":
        filtro["fecha_hora_salida"] = {"$ne": None}
    elif estado == "en_curso":
        filtro["fecha_hora_salida"] = None
    if fecha_desde or fecha_hasta:
        rango: dict = {}
        if fecha_desde:
            rango["$gte"] = fecha_desde
        if fecha_hasta:
            rango["$lte"] = fecha_hasta
        filtro["fecha_hora_entrada"] = rango

    documentos = coleccion.find(filtro).sort("fecha_hora_entrada", -1)
    return [_to_out(doc) for doc in documentos]


@router.get("/{visita_id}", response_model=VisitaOut)
def obtener_visita(visita_id: str) -> VisitaOut:
    coleccion = get_visitas_collection()
    doc = coleccion.find_one({"_id": _parse_object_id(visita_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    return _to_out(doc)


@router.patch("/{visita_id}/salida", response_model=VisitaOut)
def registrar_salida(visita_id: str) -> VisitaOut:
    coleccion = get_visitas_collection()
    oid = _parse_object_id(visita_id)
    doc = coleccion.find_one({"_id": oid})
    if doc is None:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    if doc.get("fecha_hora_salida") is not None:
        raise HTTPException(status_code=409, detail="La visita ya tiene registrada la salida")

    ahora = datetime.now(timezone.utc)
    coleccion.update_one({"_id": oid}, {"$set": {"fecha_hora_salida": ahora}})
    doc["fecha_hora_salida"] = ahora
    return _to_out(doc)
