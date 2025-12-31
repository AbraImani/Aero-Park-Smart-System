# AeroPark Smart System - Backend

## Systeme de Parking Automatise

Backend FastAPI pour la gestion d'un parking d'aeroport automatise avec integration de capteurs ESP8266.

## Fonctionnalites

- Authentification Firebase avec verification des tokens
- Gestion des places de parking (CRUD)
- Systeme de reservation avec timer automatique
- Integration capteurs ESP8266 pour detection de vehicules
- WebSocket pour mises a jour en temps reel
- Panel administration complet
- Support paiement mobile money (Orange, Airtel, M-Pesa)

## Structure du projet

```
backend/
├── main.py                 # Point d'entree
├── config.py               # Configuration
├── requirements.txt        # Dependances
├── .env.example            # Template environnement
│
├── database/
│   └── firebase.py         # Connexion Firebase
│
├── models/
│   ├── user.py             # Modeles utilisateur
│   ├── parking.py          # Modeles parking
│   ├── reservation.py      # Modeles reservation
│   ├── sensor.py           # Modeles capteur
│   └── payment.py          # Modeles paiement
│
├── routers/
│   ├── auth.py             # Endpoints authentification
│   ├── parking.py          # Endpoints parking
│   ├── admin.py            # Endpoints admin
│   ├── sensor.py           # Endpoints capteurs
│   └── websocket.py        # WebSocket temps reel
│
├── security/
│   ├── auth.py             # Verification tokens
│   └── api_key.py          # Cle API capteurs
│
├── services/
│   ├── parking_service.py      # Logique parking
│   ├── reservation_service.py  # Logique reservations
│   ├── sensor_service.py       # Logique capteurs
│   └── payment_service.py      # Logique paiements
│
└── utils/
    ├── helpers.py          # Fonctions utilitaires
    └── scheduler.py        # Planificateur expiration
```

## Installation

### 1. Creer l'environnement virtuel

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Installer les dependances

```bash
pip install -r requirements.txt
```

### 3. Configurer l'environnement

Copier `.env.example` vers `.env` et remplir les valeurs:

```bash
copy .env.example .env
```

### 4. Configurer Firebase

Telecharger le fichier de credentials depuis la console Firebase et le placer dans:
```
backend/firebase-service-account.json
```

### 5. Lancer le serveur

```bash
# Mode developpement
uvicorn main:app --reload --port 8000

# Mode production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Endpoints API

### Authentification
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/v1/users/me` | Profil utilisateur |

### Parking
| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/v1/parking/status` | Etat du parking |
| POST | `/api/v1/parking/reserve` | Reserver une place |
| POST | `/api/v1/parking/release/{id}` | Liberer une place |
| GET | `/api/v1/parking/mes-reservations` | Mes reservations |

### Administration
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/admin/parking/add` | Ajouter une place |
| DELETE | `/api/v1/admin/parking/{id}` | Supprimer une place |
| GET | `/api/v1/admin/parking/all` | Toutes les places |
| GET | `/api/v1/admin/reservations` | Reservations actives |

### Capteurs
| Methode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/sensor/update` | Signal capteur |
| GET | `/api/v1/sensor/status` | Etat des capteurs |
| GET | `/api/v1/sensor/health` | Verification sante |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `ws://host/ws/parking` | Temps reel |

## Tarification

- Tarif: 1 000 FC par heure
- Duree maximum: 168 heures (7 jours)
- Methodes: Orange Money, Airtel Money, M-Pesa

## Securite

### Utilisateurs
Header requis:
```
Authorization: Bearer <token_firebase>
```

### Capteurs
Header requis:
```
X-API-Key: <cle_api>
```

## Integration ESP8266

Exemple Arduino:

```cpp
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* endpoint = "http://serveur:8000/api/v1/sensor/update";
const char* cleApi = "votre-cle-api";

void envoyerSignal(String placeId, bool occupe) {
  HTTPClient http;
  http.begin(endpoint);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", cleApi);
  
  String payload = "{\"place_id\":\"" + placeId + "\",\"etat\":\"" + 
                   (occupe ? "occupied" : "free") + "\"}";
  
  http.POST(payload);
  http.end();
}
```

## Documentation

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

## Licence

Proprietaire - AeroPark GOMA
