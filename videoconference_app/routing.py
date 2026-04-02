"""
Zyncom - WebSocket URL Routing
================================
Maps WebSocket URLs to the ChatConsumer.
This file is imported by videoconferencing/asgi.py.
"""

from django.urls import path
from .consumers import ChatConsumer

# WebSocket URL patterns — ws/room/<room_id>/
websocket_urlpatterns = [
    path("ws/room/<str:room_id>/", ChatConsumer.as_asgi()),
]
