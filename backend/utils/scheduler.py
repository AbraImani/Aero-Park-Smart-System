# Planificateur de taches pour expiration des reservations
# =========================================================

from datetime import datetime
from loguru import logger
import asyncio


class PlanificateurReservations:
    """
    Verifie periodiquement les reservations expirees
    et les traite automatiquement.
    """
    
    def __init__(self, intervalle: int = 30):
        """
        Initialise le planificateur.
        
        Args:
            intervalle: secondes entre chaque verification
        """
        self.intervalle = intervalle
        self.en_cours = False
        self._tache: asyncio.Task = None
    
    async def demarrer(self):
        """Demarre le planificateur."""
        if self.en_cours:
            logger.warning("Le planificateur est deja en cours")
            return
        
        self.en_cours = True
        self._tache = asyncio.create_task(self._boucle_verification())
        logger.info("Planificateur de reservations demarre")
    
    async def arreter(self):
        """Arrete le planificateur."""
        self.en_cours = False
        
        if self._tache:
            self._tache.cancel()
            try:
                await self._tache
            except asyncio.CancelledError:
                pass
        
        logger.info("Planificateur de reservations arrete")
    
    async def _boucle_verification(self):
        """Boucle principale de verification."""
        while self.en_cours:
            try:
                await self._verifier_expirations()
            except Exception as e:
                logger.error(f"Erreur dans la boucle de verification: {e}")
            
            await asyncio.sleep(self.intervalle)
    
    async def _verifier_expirations(self):
        """Verifie et traite les reservations expirees."""
        from services.reservation_service import ServiceReservation
        from routers.websocket import diffuser_expiration, diffuser_mise_a_jour_place
        
        try:
            reservations = await ServiceReservation.obtenir_reservations_actives()
            maintenant = datetime.now()
            nb_expirees = 0
            
            for reservation in reservations:
                if reservation.fin and maintenant >= reservation.fin:
                    logger.info(
                        f"Reservation {reservation.id} pour place {reservation.place_id} expiree"
                    )
                    
                    # Expirer la reservation
                    await ServiceReservation.expirer_reservation(reservation.id)
                    
                    # Notifier les clients WebSocket
                    await diffuser_expiration(
                        reservation_id=reservation.id,
                        place_id=reservation.place_id,
                        utilisateur_id=reservation.utilisateur_id
                    )
                    
                    await diffuser_mise_a_jour_place(
                        place_id=reservation.place_id,
                        statut="available",
                        donnees={"raison": "expiration"}
                    )
                    
                    nb_expirees += 1
            
            if nb_expirees > 0:
                logger.info(f"{nb_expirees} reservation(s) expiree(s) traitee(s)")
        
        except Exception as e:
            logger.error(f"Erreur verification expirations: {e}")


# Instance globale
planificateur = PlanificateurReservations()


def get_planificateur() -> PlanificateurReservations:
    """Retourne le planificateur global."""
    return planificateur


async def verifier_expiration_unique(reservation_id: str) -> bool:
    """
    Verifie si une reservation specifique a expire.
    Utile pour verification immediate.
    """
    from services.reservation_service import ServiceReservation
    from routers.websocket import diffuser_expiration, diffuser_mise_a_jour_place
    
    try:
        reservation = await ServiceReservation.obtenir_reservation(reservation_id)
        
        if not reservation:
            return False
        
        if reservation.statut.value != "active":
            return False
        
        maintenant = datetime.now()
        
        if reservation.fin and maintenant >= reservation.fin:
            await ServiceReservation.expirer_reservation(reservation_id)
            
            await diffuser_expiration(
                reservation_id=reservation.id,
                place_id=reservation.place_id,
                utilisateur_id=reservation.utilisateur_id
            )
            
            await diffuser_mise_a_jour_place(
                place_id=reservation.place_id,
                statut="available",
                donnees={"raison": "expiration"}
            )
            
            return True
    
    except Exception as e:
        logger.error(f"Erreur verification expiration: {e}")
    
    return False
