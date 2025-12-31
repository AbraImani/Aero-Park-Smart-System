# Router administration
# =====================

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from security.auth import verifier_admin
from models.user import UtilisateurFirebase
from models.parking import PlaceCreate
from services.parking_service import ServiceParking

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.post("/parking/add")
async def ajouter_place(
    place: PlaceCreate,
    admin: UtilisateurFirebase = Depends(verifier_admin)
):
    """
    Ajoute une nouvelle place de parking.
    Reserve aux administrateurs.
    """
    try:
        nouvelle_place = await ServiceParking.ajouter_place(
            numero=place.numero,
            capteur_id=place.capteur_id
        )
        
        if not nouvelle_place:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La place {place.numero} existe deja"
            )
        
        logger.info(f"Admin {admin.uid} a ajoute la place {place.numero}")
        
        return {
            "succes": True,
            "message": f"Place {place.numero} ajoutee",
            "place": nouvelle_place.model_dump()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur ajout place: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'ajout de la place"
        )


@router.delete("/parking/{place_id}")
async def supprimer_place(
    place_id: str,
    admin: UtilisateurFirebase = Depends(verifier_admin)
):
    """
    Supprime une place de parking.
    La place doit etre disponible (non reservee, non occupee).
    Reserve aux administrateurs.
    """
    try:
        # Verifier que la place existe
        place = await ServiceParking.obtenir_place(place_id)
        
        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Place introuvable"
            )
        
        succes = await ServiceParking.supprimer_place(place_id)
        
        if not succes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible de supprimer cette place (peut-etre reservee ou occupee)"
            )
        
        logger.info(f"Admin {admin.uid} a supprime la place {place_id}")
        
        return {
            "succes": True,
            "message": f"Place {place_id} supprimee"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression place {place_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression"
        )


@router.get("/parking/all")
async def obtenir_toutes_places(
    admin: UtilisateurFirebase = Depends(verifier_admin)
):
    """
    Retourne toutes les places avec leurs details complets.
    Reserve aux administrateurs.
    """
    try:
        places = await ServiceParking.obtenir_toutes_places()
        
        return {
            "total": len(places),
            "places": [p.model_dump() for p in places]
        }
        
    except Exception as e:
        logger.error(f"Erreur recuperation places: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recuperation"
        )


@router.get("/reservations")
async def obtenir_toutes_reservations(
    admin: UtilisateurFirebase = Depends(verifier_admin)
):
    """
    Retourne toutes les reservations actives.
    Reserve aux administrateurs.
    """
    try:
        from services.reservation_service import ServiceReservation
        
        reservations = await ServiceReservation.obtenir_reservations_actives()
        
        return {
            "total": len(reservations),
            "reservations": [r.model_dump() for r in reservations]
        }
        
    except Exception as e:
        logger.error(f"Erreur recuperation reservations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recuperation"
        )
