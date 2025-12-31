# Point d'entree de l'application AeroPark Smart System
# ======================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys
import os

# Ajouter le dossier courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration des logs
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/aeropark.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# Imports de l'application
from config import get_settings
from database.firebase import initialiser_firebase
from routers.auth import router as router_auth
from routers.parking import router as router_parking
from routers.admin import router as router_admin
from routers.sensor import router as router_capteur
from routers.websocket import router as router_websocket
from utils.scheduler import get_planificateur

settings = get_settings()


@asynccontextmanager
async def cycle_de_vie(app: FastAPI):
    """
    Gere le demarrage et l'arret de l'application.
    """
    # === DEMARRAGE ===
    logger.info("=" * 50)
    logger.info("AeroPark Smart System - Demarrage")
    logger.info("=" * 50)
    
    # Initialiser Firebase
    try:
        initialiser_firebase()
        logger.info("Firebase initialise")
    except Exception as e:
        logger.error(f"Echec initialisation Firebase: {e}")
        raise
    
    # Creer les places par defaut si necessaire
    try:
        from services.parking_service import ServiceParking
        await ServiceParking.initialiser_places_defaut()
        logger.info("Places de parking verifiees")
    except Exception as e:
        logger.error(f"Echec initialisation places: {e}")
    
    # Demarrer le planificateur
    planificateur = get_planificateur()
    await planificateur.demarrer()
    logger.info("Planificateur demarre")
    
    logger.info("=" * 50)
    logger.info("Systeme pret")
    logger.info("=" * 50)
    
    yield
    
    # === ARRET ===
    logger.info("AeroPark Smart System - Arret")
    
    await planificateur.arreter()
    logger.info("Planificateur arrete")
    
    logger.info("Au revoir")


# Creation de l'application FastAPI
app = FastAPI(
    title="AeroPark Smart System API",
    description="""
## AeroPark GOMA - Systeme de Parking Automatise

API backend pour la gestion d'un parking d'aeroport automatise.

### Fonctionnalites

- **Authentification**: Verification des tokens Firebase
- **Gestion du parking**: Reservation et liberation des places
- **Temps reel**: WebSocket pour les mises a jour instantanees
- **Capteurs ESP8266**: Integration IoT pour detection des vehicules
- **Administration**: Gestion complete pour les administrateurs
- **Paiements**: Support Orange Money, Airtel Money, M-Pesa

### Tarification

- Tarif: 1 000 FC par heure
- Duree maximum: 168 heures (7 jours)

### Authentification

Les endpoints proteges necessitent un token Firebase dans le header:
```
Authorization: Bearer <token_firebase>
```

Les endpoints capteurs necessitent une cle API:
```
X-API-Key: <cle_api>
```
    """,
    version="1.0.0",
    contact={
        "name": "Support AeroPark",
        "email": "support@aeropark.cd"
    },
    lifespan=cycle_de_vie
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Enregistrement des routers
app.include_router(router_auth, prefix="/api/v1")
app.include_router(router_parking, prefix="/api/v1")
app.include_router(router_admin, prefix="/api/v1")
app.include_router(router_capteur, prefix="/api/v1")
app.include_router(router_websocket)


# Endpoints racine

@app.get("/", tags=["Racine"])
async def accueil():
    """Informations sur l'API."""
    return {
        "nom": "AeroPark Smart System API",
        "version": "1.0.0",
        "description": "Systeme de gestion de parking automatise",
        "statut": "operationnel",
        "documentation": "/docs",
        "tarification": {
            "tarif_heure": settings.TARIF_HEURE,
            "devise": "FC",
            "duree_max": settings.DUREE_MAX_HEURES
        }
    }


@app.get("/sante", tags=["Sante"])
async def verification_sante():
    """Verification de l'etat du systeme."""
    from utils.scheduler import get_planificateur
    from routers.websocket import get_gestionnaire_connexions
    
    planificateur = get_planificateur()
    gestionnaire_ws = get_gestionnaire_connexions()
    
    return {
        "statut": "ok",
        "services": {
            "api": "operationnel",
            "firebase": "connecte",
            "planificateur": "actif" if planificateur.en_cours else "arrete",
            "connexions_websocket": gestionnaire_ws.nombre_connexions()
        }
    }


@app.get("/api/v1", tags=["Racine"])
async def info_api():
    """Informations sur les endpoints disponibles."""
    return {
        "version": "1.0.0",
        "endpoints": {
            "utilisateurs": "/api/v1/users",
            "parking": "/api/v1/parking",
            "admin": "/api/v1/admin",
            "capteurs": "/api/v1/sensor",
            "websocket": "/ws/parking"
        }
    }


# Point d'entree pour execution directe
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
