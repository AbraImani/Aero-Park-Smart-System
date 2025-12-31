# Service de gestion des paiements
# =================================

from datetime import datetime
from typing import Optional
from loguru import logger
import uuid

from database.firebase import paiements_ref
from models.payment import Paiement, StatutPaiement, MethodePaiement, ReponsePaiement


class ServicePaiement:
    """Logique metier pour les paiements mobile money."""
    
    @staticmethod
    async def initier_paiement(
        reservation_id: str,
        utilisateur_id: str,
        montant: int,
        methode: MethodePaiement,
        telephone: str
    ) -> ReponsePaiement:
        """
        Initie un paiement mobile money.
        Dans un cas reel, cela appellerait l'API du fournisseur.
        """
        try:
            paiement_id = str(uuid.uuid4())[:8]
            reference = f"AP-{paiement_id.upper()}"
            
            paiement = Paiement(
                id=paiement_id,
                reservation_id=reservation_id,
                utilisateur_id=utilisateur_id,
                montant=montant,
                methode=methode,
                statut=StatutPaiement.EN_ATTENTE,
                telephone=telephone,
                reference_externe=reference
            )
            
            paiements_ref().document(paiement_id).set(paiement.model_dump())
            
            logger.info(
                f"Paiement {paiement_id} initie: {montant} FC via {methode.value}"
            )
            
            # Ici on simule une confirmation immediate
            # En production, on attendrait le callback du fournisseur
            await ServicePaiement.confirmer_paiement(paiement_id)
            
            return ReponsePaiement(
                succes=True,
                message="Paiement initie avec succes",
                paiement_id=paiement_id,
                montant=montant,
                reference=reference
            )
            
        except Exception as e:
            logger.error(f"Erreur initiation paiement: {e}")
            return ReponsePaiement(
                succes=False,
                message="Erreur lors du paiement"
            )
    
    @staticmethod
    async def confirmer_paiement(paiement_id: str) -> bool:
        """Confirme un paiement (appele par callback ou manuellement)."""
        try:
            paiements_ref().document(paiement_id).update({
                "statut": StatutPaiement.CONFIRME.value,
                "date_confirmation": datetime.now()
            })
            
            logger.info(f"Paiement {paiement_id} confirme")
            return True
            
        except Exception as e:
            logger.error(f"Erreur confirmation paiement {paiement_id}: {e}")
            return False
    
    @staticmethod
    async def obtenir_paiement(paiement_id: str) -> Optional[Paiement]:
        """Recupere un paiement par son ID."""
        try:
            doc = paiements_ref().document(paiement_id).get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            data["id"] = doc.id
            return Paiement(**data)
            
        except Exception as e:
            logger.error(f"Erreur recuperation paiement {paiement_id}: {e}")
            return None
    
    @staticmethod
    async def obtenir_paiements_utilisateur(utilisateur_id: str) -> list[Paiement]:
        """Recupere les paiements d'un utilisateur."""
        try:
            query = paiements_ref().where("utilisateur_id", "==", utilisateur_id)
            docs = query.get()
            
            paiements = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                paiements.append(Paiement(**data))
            
            paiements.sort(key=lambda p: p.date_creation, reverse=True)
            return paiements
            
        except Exception as e:
            logger.error(f"Erreur recuperation paiements: {e}")
            return []
    
    @staticmethod
    async def rembourser_paiement(paiement_id: str) -> bool:
        """Effectue un remboursement."""
        try:
            doc = paiements_ref().document(paiement_id).get()
            
            if not doc.exists:
                return False
            
            data = doc.to_dict()
            
            if data.get("statut") != StatutPaiement.CONFIRME.value:
                logger.warning(f"Paiement {paiement_id} non eligible au remboursement")
                return False
            
            # Ici on appellerait l'API de remboursement du fournisseur
            paiements_ref().document(paiement_id).update({
                "statut": StatutPaiement.REMBOURSE.value
            })
            
            logger.info(f"Paiement {paiement_id} rembourse")
            return True
            
        except Exception as e:
            logger.error(f"Erreur remboursement {paiement_id}: {e}")
            return False
