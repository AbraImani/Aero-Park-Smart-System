# Router WebSocket pour temps reel
# =================================

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
from datetime import datetime
from loguru import logger
import asyncio
import json

router = APIRouter(tags=["WebSocket"])


class GestionnaireConnexions:
    """Gere les connexions WebSocket pour les mises a jour en temps reel."""
    
    def __init__(self):
        self.connexions_actives: Set[WebSocket] = set()
        self._verrou = asyncio.Lock()
    
    async def connecter(self, websocket: WebSocket):
        """Accepte et enregistre une nouvelle connexion."""
        await websocket.accept()
        async with self._verrou:
            self.connexions_actives.add(websocket)
        logger.debug(f"Nouvelle connexion WebSocket. Total: {len(self.connexions_actives)}")
    
    async def deconnecter(self, websocket: WebSocket):
        """Retire une connexion."""
        async with self._verrou:
            self.connexions_actives.discard(websocket)
        logger.debug(f"Connexion WebSocket fermee. Total: {len(self.connexions_actives)}")
    
    async def diffuser(self, message: dict):
        """Envoie un message a tous les clients connectes."""
        if not self.connexions_actives:
            return
        
        texte = json.dumps(message, ensure_ascii=False, default=str)
        connexions = list(self.connexions_actives)
        
        for connexion in connexions:
            try:
                await connexion.send_text(texte)
            except Exception:
                await self.deconnecter(connexion)
    
    async def envoyer_a_client(self, websocket: WebSocket, message: dict):
        """Envoie un message a un client specifique."""
        try:
            texte = json.dumps(message, ensure_ascii=False, default=str)
            await websocket.send_text(texte)
        except Exception:
            await self.deconnecter(websocket)
    
    def nombre_connexions(self) -> int:
        """Retourne le nombre de connexions actives."""
        return len(self.connexions_actives)


# Instance globale
gestionnaire = GestionnaireConnexions()


def get_gestionnaire_connexions() -> GestionnaireConnexions:
    """Retourne le gestionnaire de connexions."""
    return gestionnaire


@router.websocket("/ws/parking")
async def websocket_parking(websocket: WebSocket):
    """
    Endpoint WebSocket pour les mises a jour en temps reel.
    
    Les clients recoivent des notifications pour:
    - Changements de statut des places
    - Mises a jour de reservations
    - Signaux des capteurs
    - Expirations de timer
    
    Format des messages:
    {
        "type": "mise_a_jour_place" | "reservation" | "capteur" | "expiration",
        "donnees": { ... },
        "timestamp": "..."
    }
    """
    await gestionnaire.connecter(websocket)
    
    try:
        # Confirmation de connexion
        await gestionnaire.envoyer_a_client(websocket, {
            "type": "connexion_etablie",
            "message": "Connecte au systeme AeroPark",
            "timestamp": datetime.now().isoformat()
        })
        
        # Boucle d'ecoute
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Traiter les differents types de messages
                type_msg = message.get("type")
                
                if type_msg == "ping":
                    await gestionnaire.envoyer_a_client(websocket, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif type_msg == "demande_etat":
                    # Le client demande l'etat actuel du parking
                    from services.parking_service import ServiceParking
                    
                    etat = await ServiceParking.obtenir_etat_parking()
                    await gestionnaire.envoyer_a_client(websocket, {
                        "type": "etat_parking",
                        "donnees": etat.model_dump(),
                        "timestamp": datetime.now().isoformat()
                    })
                
            except json.JSONDecodeError:
                await gestionnaire.envoyer_a_client(websocket, {
                    "type": "erreur",
                    "message": "Format JSON invalide"
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
    finally:
        await gestionnaire.deconnecter(websocket)


# Fonctions de diffusion pour etre appelees par les autres services

async def diffuser_mise_a_jour_place(place_id: str, statut: str, donnees: dict = None):
    """Diffuse une mise a jour de place a tous les clients."""
    message = {
        "type": "mise_a_jour_place",
        "donnees": {
            "place_id": place_id,
            "statut": statut,
            **(donnees or {})
        },
        "timestamp": datetime.now().isoformat()
    }
    await gestionnaire.diffuser(message)


async def diffuser_reservation(reservation_id: str, action: str, donnees: dict = None):
    """Diffuse une mise a jour de reservation."""
    message = {
        "type": "reservation",
        "donnees": {
            "reservation_id": reservation_id,
            "action": action,
            **(donnees or {})
        },
        "timestamp": datetime.now().isoformat()
    }
    await gestionnaire.diffuser(message)


async def diffuser_signal_capteur(place_id: str, etat: str, donnees: dict = None):
    """Diffuse un signal de capteur."""
    message = {
        "type": "capteur",
        "donnees": {
            "place_id": place_id,
            "etat": etat,
            **(donnees or {})
        },
        "timestamp": datetime.now().isoformat()
    }
    await gestionnaire.diffuser(message)


async def diffuser_expiration(reservation_id: str, place_id: str, utilisateur_id: str):
    """Diffuse une expiration de reservation."""
    message = {
        "type": "expiration",
        "donnees": {
            "reservation_id": reservation_id,
            "place_id": place_id,
            "utilisateur_id": utilisateur_id
        },
        "timestamp": datetime.now().isoformat()
    }
    await gestionnaire.diffuser(message)
