# Service de gestion des reservations
# ====================================

from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
import uuid

from database.firebase import reservations_ref, places_ref
from models.reservation import Reservation, StatutReservation, ReservationResponse
from models.parking import StatutPlace
from config import get_settings


class ServiceReservation:
    """Logique metier pour les reservations."""
    
    @staticmethod
    def calculer_montant(duree_heures: int) -> int:
        """Calcule le montant a payer pour une duree donnee."""
        settings = get_settings()
        return duree_heures * settings.TARIF_HEURE
    
    @staticmethod
    async def creer_reservation(
        place_id: str,
        utilisateur_id: str,
        duree_heures: int,
        methode_paiement: str
    ) -> ReservationResponse:
        """
        Cree une nouvelle reservation.
        Le timer demarre immediatement.
        """
        settings = get_settings()
        
        # Validation de la duree
        if duree_heures < 1 or duree_heures > settings.DUREE_MAX_HEURES:
            return ReservationResponse(
                succes=False,
                message=f"Duree invalide. Minimum 1h, maximum {settings.DUREE_MAX_HEURES}h"
            )
        
        try:
            # Verifier la disponibilite de la place
            doc = places_ref().document(place_id).get()
            
            if not doc.exists:
                return ReservationResponse(
                    succes=False,
                    message="Place introuvable"
                )
            
            place_data = doc.to_dict()
            
            if place_data.get("statut") != StatutPlace.DISPONIBLE.value:
                return ReservationResponse(
                    succes=False,
                    message="Cette place n'est plus disponible"
                )
            
            # Calculer les horaires
            maintenant = datetime.now()
            fin = maintenant + timedelta(hours=duree_heures)
            montant = ServiceReservation.calculer_montant(duree_heures)
            
            # Creer la reservation
            reservation_id = str(uuid.uuid4())[:8]
            
            reservation = Reservation(
                id=reservation_id,
                place_id=place_id,
                utilisateur_id=utilisateur_id,
                statut=StatutReservation.ACTIVE,
                debut=maintenant,
                fin=fin,
                duree_heures=duree_heures,
                montant=montant,
                methode_paiement=methode_paiement,
                paiement_confirme=True  # On suppose le paiement valide pour simplifier
            )
            
            # Sauvegarder en base
            reservations_ref().document(reservation_id).set(reservation.model_dump())
            
            # Mettre a jour le statut de la place
            places_ref().document(place_id).update({
                "statut": StatutPlace.RESERVEE.value,
                "reserve_par": utilisateur_id,
                "debut_reservation": maintenant,
                "fin_reservation": fin,
                "duree_heures": duree_heures
            })
            
            temps_restant = int((fin - maintenant).total_seconds())
            
            logger.info(
                f"Reservation {reservation_id} creee: "
                f"place {place_id}, utilisateur {utilisateur_id}, {duree_heures}h"
            )
            
            return ReservationResponse(
                succes=True,
                message="Reservation confirmee",
                reservation_id=reservation_id,
                place_numero=place_data.get("numero"),
                montant=montant,
                debut=maintenant,
                fin=fin,
                temps_restant_secondes=temps_restant
            )
            
        except Exception as e:
            logger.error(f"Erreur creation reservation: {e}")
            return ReservationResponse(
                succes=False,
                message="Erreur lors de la reservation"
            )
    
    @staticmethod
    async def obtenir_reservation(reservation_id: str) -> Optional[Reservation]:
        """Recupere une reservation par son ID."""
        try:
            doc = reservations_ref().document(reservation_id).get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data["id"] = doc.id
            return Reservation(**data)
            
        except Exception as e:
            logger.error(f"Erreur recuperation reservation {reservation_id}: {e}")
            return None
    
    @staticmethod
    async def obtenir_reservations_actives() -> list[Reservation]:
        """Recupere toutes les reservations actives."""
        try:
            query = reservations_ref().where("statut", "==", StatutReservation.ACTIVE.value)
            docs = query.get()
            
            reservations = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                reservations.append(Reservation(**data))
            
            return reservations
            
        except Exception as e:
            logger.error(f"Erreur recuperation reservations actives: {e}")
            return []
    
    @staticmethod
    async def obtenir_reservations_utilisateur(utilisateur_id: str) -> list[Reservation]:
        """Recupere les reservations d'un utilisateur."""
        try:
            query = reservations_ref().where("utilisateur_id", "==", utilisateur_id)
            docs = query.get()
            
            reservations = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                reservations.append(Reservation(**data))
            
            # Trier par date de creation decroissante
            reservations.sort(key=lambda r: r.date_creation, reverse=True)
            
            return reservations
            
        except Exception as e:
            logger.error(f"Erreur recuperation reservations utilisateur: {e}")
            return []
    
    @staticmethod
    async def expirer_reservation(reservation_id: str) -> bool:
        """Marque une reservation comme expiree et libere la place."""
        try:
            doc = reservations_ref().document(reservation_id).get()
            
            if not doc.exists:
                return False
            
            data = doc.to_dict()
            place_id = data.get("place_id")
            
            # Mettre a jour la reservation
            reservations_ref().document(reservation_id).update({
                "statut": StatutReservation.EXPIREE.value
            })
            
            # Liberer la place
            if place_id:
                places_ref().document(place_id).update({
                    "statut": StatutPlace.DISPONIBLE.value,
                    "reserve_par": None,
                    "debut_reservation": None,
                    "fin_reservation": None,
                    "duree_heures": None
                })
            
            logger.info(f"Reservation {reservation_id} expiree, place {place_id} liberee")
            return True
            
        except Exception as e:
            logger.error(f"Erreur expiration reservation {reservation_id}: {e}")
            return False
    
    @staticmethod
    async def terminer_reservation(reservation_id: str) -> bool:
        """Termine une reservation normalement (vehicule parti)."""
        try:
            doc = reservations_ref().document(reservation_id).get()
            
            if not doc.exists:
                return False
            
            data = doc.to_dict()
            place_id = data.get("place_id")
            
            # Mettre a jour la reservation
            reservations_ref().document(reservation_id).update({
                "statut": StatutReservation.TERMINEE.value
            })
            
            # Liberer la place
            if place_id:
                places_ref().document(place_id).update({
                    "statut": StatutPlace.DISPONIBLE.value,
                    "reserve_par": None,
                    "debut_reservation": None,
                    "fin_reservation": None,
                    "duree_heures": None
                })
            
            logger.info(f"Reservation {reservation_id} terminee")
            return True
            
        except Exception as e:
            logger.error(f"Erreur terminaison reservation {reservation_id}: {e}")
            return False
    
    @staticmethod
    async def annuler_reservation(reservation_id: str) -> bool:
        """Annule une reservation."""
        try:
            doc = reservations_ref().document(reservation_id).get()
            
            if not doc.exists:
                return False
            
            data = doc.to_dict()
            
            # Verifier que la reservation peut etre annulee
            if data.get("statut") not in [
                StatutReservation.EN_ATTENTE.value,
                StatutReservation.ACTIVE.value
            ]:
                logger.warning(f"Reservation {reservation_id} ne peut pas etre annulee")
                return False
            
            place_id = data.get("place_id")
            
            # Mettre a jour la reservation
            reservations_ref().document(reservation_id).update({
                "statut": StatutReservation.ANNULEE.value
            })
            
            # Liberer la place
            if place_id:
                places_ref().document(place_id).update({
                    "statut": StatutPlace.DISPONIBLE.value,
                    "reserve_par": None,
                    "debut_reservation": None,
                    "fin_reservation": None,
                    "duree_heures": None
                })
            
            logger.info(f"Reservation {reservation_id} annulee")
            return True
            
        except Exception as e:
            logger.error(f"Erreur annulation reservation {reservation_id}: {e}")
            return False
