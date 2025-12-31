# Modeles pour les capteurs ESP8266
# ==================================

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class EtatCapteur(str, Enum):
    """Etats detectes par le capteur."""
    OCCUPE = "occupied"
    LIBRE = "free"


class MiseAJourCapteur(BaseModel):
    """Donnees envoyees par un capteur ESP8266."""
    place_id: str
    etat: EtatCapteur
    force_signal: Optional[int] = None  # RSSI WiFi
    niveau_batterie: Optional[int] = None  # pourcentage


class ReponseCapteur(BaseModel):
    """Reponse du serveur au capteur."""
    succes: bool
    message: str
    place_id: str
    nouveau_statut: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class StatutCapteur(BaseModel):
    """Informations sur un capteur."""
    capteur_id: str
    place_id: str
    dernier_signal: Optional[datetime] = None
    etat_actuel: Optional[str] = None
    force_signal: Optional[int] = None
    en_ligne: bool = False
