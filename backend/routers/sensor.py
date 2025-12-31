# Router capteurs ESP8266
# =======================

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from security.api_key import verifier_cle_api
from models.sensor import MiseAJourCapteur, ReponseCapteur
from services.sensor_service import ServiceCapteur

router = APIRouter(prefix="/sensor", tags=["Capteurs ESP8266"])


@router.post("/update", response_model=ReponseCapteur)
async def recevoir_signal_capteur(
    data: MiseAJourCapteur,
    _: bool = Depends(verifier_cle_api)
):
    """
    Recoit les donnees d'un capteur ESP8266.
    
    Le capteur envoie:
    - place_id: identifiant de la place surveillee
    - etat: "occupied" ou "free"
    - force_signal: RSSI WiFi (optionnel)
    
    Necessite le header X-API-Key avec la cle valide.
    """
    logger.debug(f"Signal capteur recu: place {data.place_id}, etat {data.etat}")
    
    resultat = await ServiceCapteur.traiter_signal_capteur(data)
    
    return resultat


@router.get("/status/{place_id}")
async def obtenir_statut_capteur(
    place_id: str,
    _: bool = Depends(verifier_cle_api)
):
    """
    Retourne le statut d'un capteur specifique.
    Utile pour le diagnostic.
    """
    statut = await ServiceCapteur.obtenir_statut_capteur(place_id)
    
    if not statut:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Capteur pour la place {place_id} introuvable"
        )
    
    return {
        "succes": True,
        **statut
    }


@router.get("/status")
async def obtenir_tous_capteurs(
    _: bool = Depends(verifier_cle_api)
):
    """
    Retourne le statut de tous les capteurs.
    """
    capteurs = await ServiceCapteur.obtenir_tous_capteurs()
    
    return {
        "succes": True,
        "total": len(capteurs),
        "capteurs": capteurs
    }


@router.post("/test/{place_id}")
async def tester_capteur(
    place_id: str,
    occupe: bool,
    _: bool = Depends(verifier_cle_api)
):
    """
    Simule un signal de capteur pour les tests.
    Utile pendant le developpement sans materiel physique.
    
    - place_id: identifiant de la place
    - occupe: true si vehicule detecte, false sinon
    """
    logger.info(f"Test capteur pour place {place_id}: occupe={occupe}")
    
    resultat = await ServiceCapteur.simuler_detection(place_id, occupe)
    
    return {
        "succes": resultat.succes,
        "message": "Simulation effectuee",
        "resultat": resultat.model_dump()
    }


@router.get("/health")
async def verification_sante():
    """
    Endpoint de verification sans authentification.
    Permet aux capteurs de verifier la connectivite.
    """
    return {
        "status": "ok",
        "message": "API capteurs operationnelle"
    }
