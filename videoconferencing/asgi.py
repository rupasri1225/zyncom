"""
Zyncom - ASGI Configuration
============================
Routes HTTP requests to Django views and WebSocket connections to ChatConsumer.

How it works:
  - HTTP  → Django handles it normally (views, templates, etc.)
  - WebSocket → AuthMiddlewareStack reads the session cookie so the consumer
                knows which user is connected, then URLRouter sends it to
                ChatConsumer based on the URL pattern.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import videoconference_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'videoconferencing.settings')

application = ProtocolTypeRouter({
    # Standard HTTP requests go to Django as usual
    "http": get_asgi_application(),

    # WebSocket connections go through auth middleware then to our consumer
    "websocket": AuthMiddlewareStack(
        URLRouter(
            videoconference_app.routing.websocket_urlpatterns
        )
    ),
})
