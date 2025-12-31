# Service de gestion des capteurs ESP8266
# ========================================

from datetime import datetime
from typing import Optional
from loguru import logger

from database.firebase import capteurs_ref, places_ref
from models.sensor import MiseAJourCapteur, ReponseCapteur, EtatCapteur
from models.parking import StatutPlace


class ServiceCapteur:
    """Logique metier pour les capteurs de detection."""
    
    @staticmethod
    async def traiter_signal_capteur(data: MiseAJourCapteur) -> ReponseCapteur:
        """
        Traite un signal recu d'un capteur ESP8266.
        Met a jour le statut de la place en consequence.
        """
        try:
            place_id = data.place_id
            
            # Verifier que la place existe
            doc = places_ref().document(place_id).get()
            
            if not doc.exists:
                return ReponseCapteur(
                    succes=False,
                    message=f"Place {place_id} introuvable",
                    place_id=place_id
                )
            
            place_data = doc.to_dict()
            statut_actuel = place_data.get("statut")
            nouveau_statut = None
            
            # Logique de mise a jour selon l'etat detecte
            if data.etat == EtatCapteur.OCCUPE:
                # Vehicule detecte
                if statut_actuel == StatutPlace.RESERVEE.value:
                    # La place etait reservee, le vehicule est arrive
                    nouveau_statut = StatutPlace.OCCUPEE.value
                    places_ref().document(place_id).update({
                        "statut": nouveau_statut
                    })
                    logger.info(f"Vehicule arrive sur place {place_id}")
                    
                elif statut_actuel == StatutPlace.DISPONIBLE.value:
                    # Vehicule sans reservation (cas anormal)
                    nouveau_statut = StatutPlace.OCCUPEE.value
                    places_ref().document(place_id).update({
                        "statut": nouveau_statut
                    })
                    logger.warning(f"Vehicule detecte sans reservation sur place {place_id}")
                
            elif data.etat == EtatCapteur.LIBRE:
                # Place libre detectee
                if statut_actuel == StatutPlace.OCCUPEE.value:
                    # Le vehicule est parti
                    nouveau_statut = StatutPlace.DISPONIBLE.value
                    places_ref().document(place_id).update({
                        "statut": nouveau_statut,
                        "reserve_par": None,
                        "debut_reservation": None,
                        "fin_reservation": None,
                        "duree_heures": None
                    })
                    logger.info(f"Vehicule parti de la place {place_id}")
            
            # Enregistrer le signal du capteur
            await ServiceCapteur.enregistrer_signal(
                place_id=place_id,
                etat=data.etat.value,
                force_signal=data.force_signal
            )
            
            return ReponseCapteur(
                succes=True,
                message="Signal traite",
                place_id=place_id,
                nouveau_statut=nouveau_statut
            )
            
        except Exception as e:
            logger.error(f"Erreur traitement signal capteur: {e}")
            return ReponseCapteur(
                succes=False,
                message="Erreur de traitement",
                place_id=data.place_id
            )
    
    @staticmethod
    async def enregistrer_signal(
        place_id: str,
        etat: str,
        force_signal: int = None
    ):
        """Enregistre les donnees du capteur pour monitoring."""
        try:
            capteur_id = f"esp8266_{place_id}"
            
            capteurs_ref().document(capteur_id).set({
                "capteur_id": capteur_id,
                "place_id": place_id,
                "dernier_signal": datetime.now(),
                "etat_actuel": etat,
                "force_signal": force_signal,
                "en_ligne": True
            }, merge=True)
            
        except Exception as e:
            logger.error(f"Erreur enregistrement signal: {e}")
    
    @staticmethod
    async def obtenir_statut_capteur(place_id: str) -> Optional[dict]:
        """Recupere le statut d'un capteur."""
        try:
            capteur_id = f"esp8266_{place_id}"
            doc = capteurs_ref().document(capteur_id).get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # Verifier si le capteur est en ligne (signal dans les 5 dernieres minutes)
            dernier_signal = data.get("dernier_signal")
            if dernier_signal:
                delta = (datetime.now() - dernier_signal).total_seconds()
                data["en_ligne"] = delta < 300  # 5 minutes
            
            return data
            
        except Exception as e:
            logger.error(f"Erreur recuperation statut capteur: {e}")
            return None
    
    @staticmethod
    async def obtenir_tous_capteurs() -> list[dict]:
        """Recupere le statut de tous les capteurs."""
        try:
            docs = capteurs_ref().get()
            capteurs = []
            
            for doc in docs:
                data = doc.to_dict()
                
                # Verifier si en ligne
                dernier_signal = data.get("dernier_signal")
                if dernier_signal:
                    delta = (datetime.now() - dernier_signal).total_seconds()
                    data["en_ligne"] = delta < 300
                
                capteurs.append(data)
            
            return capteurs
            
        except Exception as e:
            logger.error(f"Erreur recuperation capteurs: {e}")
            return []
    
    @staticmethod
    async def simuler_detection(place_id: str, occupe: bool) -> ReponseCapteur:
        """
        Simule un signal de capteur pour les tests.
        Utile pendant le developpement.
        """
        etat = EtatCapteur.OCCUPE if occupe else EtatCapteur.LIBRE
        
        signal = MiseAJourCapteur(
            place_id=place_id,
            etat=etat,
            force_signal=-50  # Signal simule
        )
        
        return await ServiceCapteur.traiter_signal_capteur(signal)
