# Authentification et verification des tokens Firebase
# =====================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from loguru import logger

from models.user import UtilisateurFirebase, RoleUtilisateur
from database.firebase import utilisateurs_ref

# Schema de securite Bearer
schema_bearer = HTTPBearer(auto_error=False)


async def verifier_token(
    credentials: HTTPAuthorizationCredentials = Depends(schema_bearer)
) -> UtilisateurFirebase:
    """
    Verifie le token Firebase et retourne les infos utilisateur.
    Leve une exception si le token est invalide ou absent.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token d'authentification requis",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    try:
        # Verification du token aupres de Firebase
        token_decode = auth.verify_id_token(token)
        
        utilisateur = UtilisateurFirebase(
            uid=token_decode["uid"],
            email=token_decode.get("email"),
            nom=token_decode.get("name"),
            email_verifie=token_decode.get("email_verified", False)
        )
        
        return utilisateur
        
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expire, veuillez vous reconnecter"
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoque"
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )
    except Exception as e:
        logger.error(f"Erreur verification token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Echec de l'authentification"
        )


async def get_utilisateur_courant(
    utilisateur: UtilisateurFirebase = Depends(verifier_token)
) -> UtilisateurFirebase:
    """
    Dependance pour obtenir l'utilisateur connecte.
    Alias plus explicite de verifier_token.
    """
    return utilisateur


async def get_role_utilisateur(uid: str) -> RoleUtilisateur:
    """
    Recupere le role d'un utilisateur depuis Firestore.
    Retourne USER par defaut si non trouve.
    """
    try:
        doc = utilisateurs_ref().document(uid).get()
        if doc.exists:
            data = doc.to_dict()
            role_str = data.get("role", "user")
            return RoleUtilisateur(role_str)
    except Exception as e:
        logger.warning(f"Impossible de recuperer le role pour {uid}: {e}")
    
    return RoleUtilisateur.USER


async def verifier_admin(
    utilisateur: UtilisateurFirebase = Depends(verifier_token)
) -> UtilisateurFirebase:
    """
    Verifie que l'utilisateur est un administrateur.
    Leve une exception 403 si ce n'est pas le cas.
    """
    role = await get_role_utilisateur(utilisateur.uid)
    
    if role != RoleUtilisateur.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acces reserve aux administrateurs"
        )
    
    return utilisateur
