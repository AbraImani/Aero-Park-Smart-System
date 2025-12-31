# Package des routers
# ===================

from routers.auth import router as router_auth
from routers.parking import router as router_parking
from routers.admin import router as router_admin
from routers.sensor import router as router_capteur
from routers.websocket import router as router_websocket

__all__ = [
    "router_auth",
    "router_parking",
    "router_admin",
    "router_capteur",
    "router_websocket"
]
