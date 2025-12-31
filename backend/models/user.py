# Modeles utilisateur
# ===================

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class RoleUtilisateur(str, Enum):
    """Roles disponibles dans le systeme."""
    ADMIN = "admin"
    USER = "user"


class UtilisateurBase(BaseModel):
    """Donnees de base d'un utilisateur."""
    email: EmailStr
    nom: str = Field(min_length=2, max_length=100)
    telephone: Optional[str] = None


class UtilisateurCreate(UtilisateurBase):
    """Donnees pour creer un utilisateur."""
    mot_de_passe: str = Field(min_length=6)


class Utilisateur(UtilisateurBase):
    """Utilisateur complet avec toutes ses informations."""
    id: str
    role: RoleUtilisateur = RoleUtilisateur.USER
    date_creation: datetime = Field(default_factory=datetime.now)
    actif: bool = True
    
    class Config:
        from_attributes = True


class UtilisateurFirebase(BaseModel):
    """Donnees extraites du token Firebase."""
    uid: str
    email: Optional[str] = None
    nom: Optional[str] = None
    email_verifie: bool = False
    
    class Config:
        from_attributes = True


class ProfilUtilisateur(BaseModel):
    """Profil utilisateur pour affichage."""
    id: str
    email: str
    nom: Optional[str] = None
    role: str
    reservations_actives: int = 0
