# Verification des cles API pour les capteurs
# ============================================

from fastapi import Header, HTTPException, status
from config import get_settings


async def verifier_cle_api(
    x_api_key: str = Header(None, alias="X-API-Key")
) -> bool:
    """
    Verifie la cle API envoyee par les capteurs ESP8266.
    La cle doit etre presente dans le header X-API-Key.
    """
    settings = get_settings()
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cle API requise dans le header X-API-Key"
        )
    
    if x_api_key != settings.SENSOR_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cle API invalide"
        )
    
    return True
