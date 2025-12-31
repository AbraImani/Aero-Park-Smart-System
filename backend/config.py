# Configuration du backend AeroPark
# ==================================

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import json


class Settings(BaseSettings):
    """Configuration centralisee de l'application."""
    
    # Mode debug
    DEBUG: bool = False
    
    # Firebase
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CREDENTIALS_PATH: str = "firebase-service-account.json"
    
    # Cle API pour les capteurs ESP8266
    SENSOR_API_KEY: str = "aeropark-sensor-key-2024"
    
    # CORS - origines autorisees
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ]
    
    # Tarification
    TARIF_HEURE: int = 1000  # 1000 FC par heure
    DUREE_MAX_HEURES: int = 168  # 7 jours maximum
    
    # Intervalle de verification des expirations (secondes)
    INTERVALLE_VERIFICATION: int = 30
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def get_cors_origins(self) -> List[str]:
        """Retourne la liste des origines CORS."""
        return self.CORS_ORIGINS


@lru_cache()
def get_settings() -> Settings:
    """Retourne l'instance unique de configuration."""
    return Settings()
