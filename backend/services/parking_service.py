# Service de gestion des places de parking
# =========================================

from datetime import datetime
from typing import Optional
from loguru import logger

from database.firebase import places_ref
from models.parking import PlaceParking, StatutPlace, PlaceResponse, EtatParking
from config import get_settings


class ServiceParking:
    """Logique metier pour la gestion des places de parking."""
    
    @staticmethod
    async def initialiser_places_defaut():
        """
        Cree les 5 places de parking par defaut si elles n'existent pas.
        Appelee au demarrage de l'application.
        """
        try:
            collection = places_ref()
            docs = collection.limit(1).get()
            
            # Si des places existent deja, ne rien faire
            if len(list(docs)) > 0:
                logger.info("Places de parking deja initialisees")
                return
            
            # Creer les 5 places par defaut
            places_defaut = ["A1", "A2", "A3", "A4", "A5"]
            
            for numero in places_defaut:
                place = PlaceParking(
                    id=numero.lower(),
                    numero=numero,
                    statut=StatutPlace.DISPONIBLE,
                    capteur_id=f"esp8266_{numero.lower()}"
                )
                collection.document(place.id).set(place.model_dump())
            
            logger.info(f"Creation de {len(places_defaut)} places de parking")
            
        except Exception as e:
            logger.error(f"Erreur initialisation places: {e}")
    
    @staticmethod
    async def obtenir_toutes_places() -> list[PlaceParking]:
        """Recupere toutes les places de parking."""
        try:
            docs = places_ref().get()
            places = []
            
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                places.append(PlaceParking(**data))
            
            return places
            
        except Exception as e:
            logger.error(f"Erreur recuperation places: {e}")
            return []
    
    @staticmethod
    async def obtenir_place(place_id: str) -> Optional[PlaceParking]:
        """Recupere une place par son ID."""
        try:
            doc = places_ref().document(place_id).get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data["id"] = doc.id
            return PlaceParking(**data)
            
        except Exception as e:
            logger.error(f"Erreur recuperation place {place_id}: {e}")
            return None
    
    @staticmethod
    async def obtenir_etat_parking() -> EtatParking:
        """Retourne l'etat global du parking."""
        places = await ServiceParking.obtenir_toutes_places()
        
        disponibles = sum(1 for p in places if p.statut == StatutPlace.DISPONIBLE)
        reservees = sum(1 for p in places if p.statut == StatutPlace.RESERVEE)
        occupees = sum(1 for p in places if p.statut == StatutPlace.OCCUPEE)
        
        # Convertir en reponses avec temps restant
        places_response = []
        maintenant = datetime.now()
        
        for place in places:
            temps_restant = None
            if place.fin_reservation and place.statut in [StatutPlace.RESERVEE, StatutPlace.OCCUPEE]:
                delta = (place.fin_reservation - maintenant).total_seconds()
                temps_restant = max(0, int(delta))
            
            places_response.append(PlaceResponse(
                id=place.id,
                numero=place.numero,
                statut=place.statut.value,
                reserve_par=place.reserve_par,
                temps_restant=temps_restant,
                peut_reserver=place.statut == StatutPlace.DISPONIBLE
            ))
        
        return EtatParking(
            total_places=len(places),
            places_disponibles=disponibles,
            places_reservees=reservees,
            places_occupees=occupees,
            places=places_response
        )
    
    @staticmethod
    async def mettre_a_jour_statut(
        place_id: str,
        statut: StatutPlace,
        utilisateur_id: str = None,
        debut: datetime = None,
        fin: datetime = None,
        duree: int = None
    ) -> bool:
        """Met a jour le statut d'une place."""
        try:
            updates = {"statut": statut.value}
            
            if utilisateur_id is not None:
                updates["reserve_par"] = utilisateur_id
            if debut is not None:
                updates["debut_reservation"] = debut
            if fin is not None:
                updates["fin_reservation"] = fin
            if duree is not None:
                updates["duree_heures"] = duree
            
            places_ref().document(place_id).update(updates)
            return True
            
        except Exception as e:
            logger.error(f"Erreur mise a jour place {place_id}: {e}")
            return False
    
    @staticmethod
    async def liberer_place(place_id: str) -> bool:
        """Libere une place de parking (remet a disponible)."""
        try:
            places_ref().document(place_id).update({
                "statut": StatutPlace.DISPONIBLE.value,
                "reserve_par": None,
                "debut_reservation": None,
                "fin_reservation": None,
                "duree_heures": None
            })
            return True
            
        except Exception as e:
            logger.error(f"Erreur liberation place {place_id}: {e}")
            return False
    
    @staticmethod
    async def ajouter_place(numero: str, capteur_id: str = None) -> Optional[PlaceParking]:
        """Ajoute une nouvelle place de parking."""
        try:
            place_id = numero.lower().replace(" ", "_")
            
            # Verifier si la place existe deja
            doc = places_ref().document(place_id).get()
            if doc.exists:
                logger.warning(f"Place {numero} existe deja")
                return None
            
            place = PlaceParking(
                id=place_id,
                numero=numero,
                statut=StatutPlace.DISPONIBLE,
                capteur_id=capteur_id or f"esp8266_{place_id}"
            )
            
            places_ref().document(place_id).set(place.model_dump())
            logger.info(f"Place {numero} ajoutee")
            
            return place
            
        except Exception as e:
            logger.error(f"Erreur ajout place: {e}")
            return None
    
    @staticmethod
    async def supprimer_place(place_id: str) -> bool:
        """Supprime une place de parking."""
        try:
            doc = places_ref().document(place_id).get()
            
            if not doc.exists:
                return False
            
            # Verifier que la place n'est pas reservee ou occupee
            data = doc.to_dict()
            if data.get("statut") != StatutPlace.DISPONIBLE.value:
                logger.warning(f"Impossible de supprimer la place {place_id}: non disponible")
                return False
            
            places_ref().document(place_id).delete()
            logger.info(f"Place {place_id} supprimee")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur suppression place {place_id}: {e}")
            return False
