"""Modelos Pydantic para el registro de visitas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class VisitaCreate(BaseModel):
    nombre_visitante: str
    dni: str
    motivo: str
    area_visitada: str
    persona_visitada: str


class VisitaOut(BaseModel):
    id: str
    nombre_visitante: str
    dni: str
    motivo: str
    area_visitada: str
    persona_visitada: str
    fecha_hora_entrada: datetime
    fecha_hora_salida: Optional[datetime] = None
    estado: str = Field(description="'en_curso' o 'finalizada'")
