# Router authentification
# =======================

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from security.auth import get_utilisateur_courant, get_role_utilisateur
from models.user import UtilisateurFirebase, ProfilUtilisateur
from services.reservation_service import ServiceReservation

router = APIRouter(prefix="/users", tags=["Utilisateurs"])


@router.get("/me", response_model=ProfilUtilisateur)
async def obtenir_profil(
    utilisateur: UtilisateurFirebase = Depends(get_utilisateur_courant)
):
    """
    Retourne le profil de l'utilisateur connecte.
    Necessite un token Firebase valide.
    """
    try:
        # Recuperer le role
        role = await get_role_utilisateur(utilisateur.uid)
        
        # Compter les reservations actives
        reservations = await ServiceReservation.obtenir_reservations_utilisateur(
            utilisateur.uid
        )
        reservations_actives = sum(
            1 for r in reservations if r.statut.value == "active"
        )
        
        return ProfilUtilisateur(
            id=utilisateur.uid,
            email=utilisateur.email or "",
            nom=utilisateur.nom,
            role=role.value,
            reservations_actives=reservations_actives
        )
        
    except Exception as e:
        logger.error(f"Erreur recuperation profil: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recuperation du profil"
        )
