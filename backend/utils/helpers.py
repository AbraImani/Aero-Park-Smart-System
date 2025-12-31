# Fonctions utilitaires
# =====================

from datetime import datetime, timedelta
from typing import Optional
import re


def formater_duree(heures: int) -> str:
    """Formate une duree en heures vers un texte lisible."""
    if heures < 24:
        return f"{heures}h"
    
    jours = heures // 24
    reste = heures % 24
    
    if reste == 0:
        return f"{jours}j"
    return f"{jours}j {reste}h"


def formater_prix(montant: int) -> str:
    """Formate un montant en Francs Congolais."""
    texte = "{:,}".format(montant).replace(",", " ")
    return f"{texte} FC"


def calculer_prix(heures: int, tarif: int = 1000) -> int:
    """Calcule le prix total pour une duree donnee."""
    return heures * tarif


def calculer_fin_reservation(debut: datetime, duree_heures: int) -> datetime:
    """Calcule la date de fin d'une reservation."""
    return debut + timedelta(hours=duree_heures)


def calculer_temps_restant(fin: datetime) -> dict:
    """
    Calcule le temps restant jusqu'a une date.
    Retourne un dictionnaire avec heures, minutes, secondes.
    """
    maintenant = datetime.now()
    
    if maintenant >= fin:
        return {
            "expire": True,
            "heures": 0,
            "minutes": 0,
            "secondes": 0,
            "total_secondes": 0
        }
    
    delta = fin - maintenant
    total = int(delta.total_seconds())
    
    heures = total // 3600
    minutes = (total % 3600) // 60
    secondes = total % 60
    
    return {
        "expire": False,
        "heures": heures,
        "minutes": minutes,
        "secondes": secondes,
        "total_secondes": total
    }


def formater_temps_restant(fin: datetime) -> str:
    """Formate le temps restant en texte."""
    restant = calculer_temps_restant(fin)
    
    if restant["expire"]:
        return "Expire"
    
    parties = []
    if restant["heures"] > 0:
        parties.append(f"{restant['heures']}h")
    if restant["minutes"] > 0:
        parties.append(f"{restant['minutes']}min")
    if restant["secondes"] > 0 or not parties:
        parties.append(f"{restant['secondes']}s")
    
    return " ".join(parties)


def valider_telephone(numero: str) -> bool:
    """Verifie le format d'un numero de telephone RDC."""
    nettoye = re.sub(r'[\s\-]', '', numero)
    
    patterns = [
        r'^\+243[0-9]{9}$',  # Format international
        r'^243[0-9]{9}$',    # Sans le +
        r'^0[0-9]{9}$'       # Format local
    ]
    
    return any(re.match(p, nettoye) for p in patterns)


def formater_telephone(numero: str) -> str:
    """Convertit un numero vers le format international."""
    nettoye = re.sub(r'[\s\-]', '', numero)
    
    if nettoye.startswith('+243'):
        return nettoye
    elif nettoye.startswith('243'):
        return f'+{nettoye}'
    elif nettoye.startswith('0'):
        return f'+243{nettoye[1:]}'
    
    return nettoye


def valider_id_place(place_id: str) -> bool:
    """Verifie le format d'un identifiant de place."""
    pattern = r'^[A-Za-z][0-9]+$'
    return bool(re.match(pattern, place_id))


def generer_id_place(prefixe: str, numero: int) -> str:
    """Genere un identifiant de place."""
    return f"{prefixe.upper()}{numero}"


def nettoyer_texte(texte: str) -> str:
    """Nettoie un texte pour stockage."""
    if not texte:
        return ""
    
    texte = texte.strip()
    texte = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', texte)
    
    return texte


def parser_datetime(chaine: str) -> Optional[datetime]:
    """Parse une chaine de date dans differents formats."""
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(chaine, fmt)
        except ValueError:
            continue
    
    return None


def datetime_vers_iso(dt: datetime) -> str:
    """Convertit une datetime vers ISO 8601."""
    return dt.isoformat()


def timestamp_actuel() -> str:
    """Retourne le timestamp actuel en ISO 8601."""
    return datetime.now().isoformat()
