"""
Zyncom - HTTP URL Patterns
============================
All URL routes for the Zyncom platform.

Grouped into:
  1. Public pages      — no login required
  2. Auth pages        — login / register / logout
  3. Dashboard         — room management
  4. Room workspace    — the main meeting page
  5. AJAX endpoints    — called by JavaScript (return JSON)
  6. File serving      — authenticated file downloads
"""

from django.urls import path
from . import views

urlpatterns = [

    # ── 1. Public pages ──────────────────────────────────────────────────────
    path('',            views.index,    name='index'),
    path('features/',   views.features, name='features'),
    path('contact/',    views.contact,  name='contact'),

    # ── 2. Auth pages ────────────────────────────────────────────────────────
    path('register/',   views.register,     name='register'),
    path('login/',      views.login_view,   name='login'),
    path('logout/',     views.logout_view,  name='logout'),

    # ── 3. Dashboard ─────────────────────────────────────────────────────────
    # GET  /dashboard/        — list all rooms the user has joined
    # POST /room/create/      — create a new room
    # POST /room/join/        — join an existing room by room_id
    path('dashboard/',      views.dashboard,    name='dashboard'),
    path('room/create/',    views.create_room,  name='create_room'),
    path('room/join/',      views.join_room,    name='join_room'),

    # ── 4. Room workspace ────────────────────────────────────────────────────
    # GET /room/<room_id>/    — open the workspace for a specific room
    path('room/<str:room_id>/', views.workspace, name='workspace'),

    # ── 5. AJAX endpoints (return JSON, called by JavaScript) ────────────────

    # Save or update the current user's notes for a room
    # POST /room/<room_id>/note/save/
    path('room/<str:room_id>/note/save/',
         views.save_note,
         name='save_note'),

    # Upload a file to a room
    # POST /room/<room_id>/file/upload/
    path('room/<str:room_id>/file/upload/',
         views.upload_file,
         name='upload_file'),

    # Toggle recording on/off (host only)
    # POST /room/<room_id>/recording/toggle/
    path('room/<str:room_id>/recording/toggle/',
         views.toggle_recording,
         name='toggle_recording'),

    # Remove a participant from the room (host only)
    # POST /room/<room_id>/remove/<username>/
    path('room/<str:room_id>/remove/<str:username>/',
         views.remove_participant,
         name='remove_participant'),

    # End the meeting for everyone (host only)
    # POST /room/<room_id>/end/
    path('room/<str:room_id>/end/',
         views.end_meeting,
         name='end_meeting'),

    # ── 6. File serving ──────────────────────────────────────────────────────
    # Authenticated download — checks room membership before serving
    # GET /files/<file_id>/
    path('files/<int:file_id>/',
         views.serve_file,
         name='serve_file'),
]
