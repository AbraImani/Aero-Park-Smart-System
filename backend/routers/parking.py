# Router parking
# ==============

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from security.auth import get_utilisateur_courant
from models.user import UtilisateurFirebase
from models.parking import EtatParking
from models.reservation import ReservationCreate, ReservationResponse
from services.parking_service import ServiceParking
from services.reservation_service import ServiceReservation

router = APIRouter(prefix="/parking", tags=["Parking"])


@router.get("/status", response_model=EtatParking)
async def obtenir_etat_parking(
    utilisateur: UtilisateurFirebase = Depends(get_utilisateur_courant)
):
    """
    Retourne l'etat actuel de toutes les places de parking.
    Inclut le nombre de places disponibles et le temps restant pour chaque reservation.
    """
    try:
        etat = await ServiceParking.obtenir_etat_parking()
        return etat
        
    except Exception as e:
        logger.error(f"Erreur recuperation etat parking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recuperation de l'etat du parking"
        )


@router.post("/reserve", response_model=ReservationResponse)
async def reserver_place(
    reservation: ReservationCreate,
    utilisateur: UtilisateurFirebase = Depends(get_utilisateur_courant)
):
    """
    Reserve une place de parking.
    Le timer demarre immediatement apres la reservation.
    
    - place_id: identifiant de la place
    - duree_heures: duree souhaitee (1 a 168 heures)
    - methode_paiement: orange_money, airtel_money ou mpesa
    """
    try:
        resultat = await ServiceReservation.creer_reservation(
            place_id=reservation.place_id,
            utilisateur_id=utilisateur.uid,
            duree_heures=reservation.duree_heures,
            methode_paiement=reservation.methode_paiement
        )
        
        if not resultat.succes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resultat.message
            )
        
        return resultat
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur reservation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la reservation"
        )


@router.post("/release/{place_id}")
async def liberer_place(
    place_id: str,
    utilisateur: UtilisateurFirebase = Depends(get_utilisateur_courant)
):
    """
    Libere une place de parking.
    Seul le proprietaire de la reservation peut liberer la place.
    """
    try:
        # Verifier que la place appartient a l'utilisateur
        place = await ServiceParking.obtenir_place(place_id)
        
        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Place introuvable"
            )
        
        if place.reserve_par != utilisateur.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez pas liberer cette place"
            )
        
        # Liberer la place
        succes = await ServiceParking.liberer_place(place_id)
        
        if not succes:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erreur lors de la liberation"
            )
        
        return {
            "succes": True,
            "message": f"Place {place.numero} liberee"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur liberation place {place_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la liberation"
        )


@router.get("/mes-reservations")
async def obtenir_mes_reservations(
    utilisateur: UtilisateurFirebase = Depends(get_utilisateur_courant)
):
    """
    Retourne l'historique des reservations de l'utilisateur.
    """
    try:
        reservations = await ServiceReservation.obtenir_reservations_utilisateur(
            utilisateur.uid
        )
        
        return {
            "total": len(reservations),
            "reservations": [r.model_dump() for r in reservations]
        }
        
    except Exception as e:
        logger.error(f"Erreur recuperation reservations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recuperation des reservations"
        )
