# Modeles pour les paiements
# ===========================

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class MethodePaiement(str, Enum):
    """Methodes de paiement acceptees."""
    ORANGE_MONEY = "orange_money"
    AIRTEL_MONEY = "airtel_money"
    MPESA = "mpesa"


class StatutPaiement(str, Enum):
    """Etats d'un paiement."""
    EN_ATTENTE = "pending"
    CONFIRME = "confirmed"
    ECHOUE = "failed"
    REMBOURSE = "refunded"


class Paiement(BaseModel):
    """Enregistrement d'un paiement."""
    id: str
    reservation_id: str
    utilisateur_id: str
    montant: int  # en FC
    methode: MethodePaiement
    statut: StatutPaiement = StatutPaiement.EN_ATTENTE
    telephone: str
    reference_externe: Optional[str] = None  # reference du mobile money
    date_creation: datetime = Field(default_factory=datetime.now)
    date_confirmation: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DemandePaiement(BaseModel):
    """Requete pour initier un paiement."""
    reservation_id: str
    methode: MethodePaiement
    telephone: str = Field(min_length=10, max_length=15)


class ReponsePaiement(BaseModel):
    """Reponse apres traitement du paiement."""
    succes: bool
    message: str
    paiement_id: Optional[str] = None
    montant: Optional[int] = None
    reference: Optional[str] = None
