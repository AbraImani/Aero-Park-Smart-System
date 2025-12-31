# Modeles pour les places de parking
# ===================================

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class StatutPlace(str, Enum):
    """Etats possibles d'une place de parking."""
    DISPONIBLE = "available"
    RESERVEE = "reserved"
    OCCUPEE = "occupied"


class PlaceParking(BaseModel):
    """Representation d'une place de parking."""
    id: str
    numero: str  # ex: A1, A2, B1
    statut: StatutPlace = StatutPlace.DISPONIBLE
    reserve_par: Optional[str] = None  # ID utilisateur
    debut_reservation: Optional[datetime] = None
    fin_reservation: Optional[datetime] = None
    duree_heures: Optional[int] = None
    capteur_id: Optional[str] = None
    date_creation: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class PlaceCreate(BaseModel):
    """Donnees pour ajouter une place."""
    numero: str = Field(min_length=1, max_length=10)
    capteur_id: Optional[str] = None


class PlaceResponse(BaseModel):
    """Reponse avec les infos d'une place."""
    id: str
    numero: str
    statut: str
    reserve_par: Optional[str] = None
    temps_restant: Optional[int] = None  # en secondes
    peut_reserver: bool = True


class EtatParking(BaseModel):
    """Etat global du parking."""
    total_places: int
    places_disponibles: int
    places_reservees: int
    places_occupees: int
    places: list[PlaceResponse]
