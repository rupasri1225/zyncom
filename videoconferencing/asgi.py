import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from whitenoise import WhiteNoise
import videoconference_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'videoconferencing.settings')

# Create Django ASGI app
django_asgi_app = get_asgi_application()

# 🔥 Wrap with WhiteNoise (THIS FIXES STATIC)
django_asgi_app = WhiteNoise(django_asgi_app)

application = ProtocolTypeRouter({
    "http": django_asgi_app,  # ✅ NOW STATIC WORKS
    "websocket": AuthMiddlewareStack(
        URLRouter(
            videoconference_app.routing.websocket_urlpatterns
        )
    ),
})