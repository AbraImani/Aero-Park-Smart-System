# Connexion Firebase et gestion des collections
# ==============================================

import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore import AsyncClient
from loguru import logger
import os

# Variable globale pour l'etat d'initialisation
_firebase_initialise = False
_db = None


def initialiser_firebase():
    """
    Initialise la connexion a Firebase.
    Peut etre appelee plusieurs fois sans effet si deja initialise.
    """
    global _firebase_initialise, _db
    
    if _firebase_initialise:
        return
    
    try:
        # Essayer d'abord avec le fichier de credentials
        chemin_credentials = os.getenv(
            "FIREBASE_CREDENTIALS_PATH",
            "firebase-service-account.json"
        )
        
        if os.path.exists(chemin_credentials):
            cred = credentials.Certificate(chemin_credentials)
            firebase_admin.initialize_app(cred)
            logger.info(f"Firebase initialise avec le fichier: {chemin_credentials}")
        else:
            # Sinon utiliser les variables d'environnement
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
            client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
            
            if not all([project_id, private_key, client_email]):
                raise ValueError(
                    "Configuration Firebase incomplete. "
                    "Fournir soit le fichier credentials, soit les variables d'environnement."
                )
            
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": project_id,
                "private_key": private_key,
                "client_email": client_email,
                "token_uri": "https://oauth2.googleapis.com/token"
            })
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialise avec les variables d'environnement")
        
        _db = firestore.client()
        _firebase_initialise = True
        
    except Exception as e:
        logger.error(f"Echec initialisation Firebase: {e}")
        raise


def get_db():
    """Retourne le client Firestore."""
    global _db
    if not _firebase_initialise:
        initialiser_firebase()
    return _db


# Noms des collections Firestore
class Collections:
    """Noms des collections dans Firestore."""
    UTILISATEURS = "utilisateurs"
    PLACES = "places_parking"
    RESERVATIONS = "reservations"
    PAIEMENTS = "paiements"
    CAPTEURS = "capteurs"
    LOGS = "logs_systeme"


def get_collection(nom: str):
    """Retourne une reference vers une collection."""
    return get_db().collection(nom)


def places_ref():
    """Reference vers la collection des places de parking."""
    return get_collection(Collections.PLACES)


def reservations_ref():
    """Reference vers la collection des reservations."""
    return get_collection(Collections.RESERVATIONS)


def utilisateurs_ref():
    """Reference vers la collection des utilisateurs."""
    return get_collection(Collections.UTILISATEURS)


def paiements_ref():
    """Reference vers la collection des paiements."""
    return get_collection(Collections.PAIEMENTS)


def capteurs_ref():
    """Reference vers la collection des capteurs."""
    return get_collection(Collections.CAPTEURS)
