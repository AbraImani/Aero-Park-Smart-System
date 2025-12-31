# Modeles pour les reservations
# ==============================

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class StatutReservation(str, Enum):
    """Etats possibles d'une reservation."""
    EN_ATTENTE = "pending"      # Paiement en attente
    ACTIVE = "active"           # Reservation confirmee
    EXPIREE = "expired"         # Temps ecoule sans arrivee
    TERMINEE = "completed"      # Vehicule parti normalement
    ANNULEE = "cancelled"


class ReservationCreate(BaseModel):
    """Donnees pour creer une reservation."""
    place_id: str
    duree_heures: int = Field(ge=1, le=168)  # 1h minimum, 7 jours max
    methode_paiement: str


class Reservation(BaseModel):
    """Reservation complete."""
    id: str
    place_id: str
    utilisateur_id: str
    statut: StatutReservation = StatutReservation.EN_ATTENTE
    debut: datetime
    fin: datetime
    duree_heures: int
    montant: int  # en FC
    methode_paiement: str
    paiement_confirme: bool = False
    vehicule_arrive: bool = False
    date_creation: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class ReservationResponse(BaseModel):
    """Reponse apres reservation."""
    succes: bool
    message: str
    reservation_id: Optional[str] = None
    place_numero: Optional[str] = None
    montant: Optional[int] = None
    debut: Optional[datetime] = None
    fin: Optional[datetime] = None
    temps_restant_secondes: Optional[int] = None


class DemandeLiberation(BaseModel):
    """Demande de liberation d'une place."""
    place_id: str
    raison: Optional[str] = None
