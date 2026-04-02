"""
Zyncom - Views
===============
All HTTP view functions for the Zyncom platform.

Tasks 4 & 5 implement the core and AJAX views.
Auth views (register, login, logout) are kept from the original project.
"""

import uuid
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, FileResponse, Http404
from django.db import IntegrityError
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .forms import RegisterForm
from .models import Room, Message, Note, SharedFile


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _generate_room_id():
    """Generate a short unique 8-character room ID."""
    return str(uuid.uuid4())[:8]


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC PAGES
# ─────────────────────────────────────────────────────────────────────────────

def index(request):
    return render(request, 'index.html')


def features(request):
    return render(request, 'features.html')


def contact(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '')
        email   = request.POST.get('email', '')
        message = request.POST.get('message', '')
        subject = f"New Contact Message from {name}"
        body    = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        try:
            send_mail(subject, body, 'your_email@gmail.com',
                      ['chakravarthy.atipamula@gmail.com'], fail_silently=False)
            return JsonResponse({'status': 'success', 'message': 'Message sent!'})
        except Exception:
            return JsonResponse({'status': 'error', 'message': 'Failed to send.'})
    return render(request, 'contact.html')


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                return render(request, 'login.html',
                              {'success': "Registration successful. Please login."})
            except IntegrityError:
                return render(request, 'register.html',
                              {'error': "User already exists.", 'form': form})
        return render(request, 'register.html',
                      {'error': form.errors.as_text(), 'form': form})
    return render(request, 'register.html', {'form': RegisterForm()})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('email')   # form uses "email" field for username
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        return render(request, 'login.html', {'error': "Invalid credentials"})
    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4.1 — DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    """
    Show all rooms the logged-in user has joined, newest first.
    The template can use {{ rooms }} to render room cards.
    """
    # Get all rooms where the current user is a member, newest first
    rooms = Room.objects.filter(members=request.user).order_by('-created_at')

    return render(request, 'dashboard.html', {
        'rooms': rooms,
        'username': request.user.username,
    })


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4.2 — CREATE ROOM
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def create_room(request):
    """
    Create a new room and redirect to its workspace.

    - Generates a unique 8-character room_id
    - Sets the logged-in user as created_by (the host)
    - Adds the user to members so they appear in their dashboard
    """
    if request.method == 'POST':
        room_name = request.POST.get('name', '').strip()

        # Validate: room name must not be empty
        if not room_name:
            rooms = Room.objects.filter(members=request.user).order_by('-created_at')
            return render(request, 'dashboard.html', {
                'rooms': rooms,
                'username': request.user.username,
                'create_error': "Room name cannot be empty.",
            })

        # Generate a unique room_id (retry if collision — extremely rare)
        room_id = _generate_room_id()
        while Room.objects.filter(room_id=room_id).exists():
            room_id = _generate_room_id()

        # Create the room — the creator is automatically the host
        room = Room.objects.create(
            room_id=room_id,
            name=room_name,
            created_by=request.user,
        )

        # Add the creator to members so the room shows on their dashboard
        room.members.add(request.user)

        # Redirect to the workspace for this new room
        return redirect('workspace', room_id=room_id)

    # GET request — just redirect to dashboard (form is on dashboard page)
    return redirect('dashboard')


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4.3 — JOIN ROOM
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def join_room(request):
    """
    Join an existing room using its room_id.

    - Looks up the room by room_id (404 if not found)
    - Adds the user to members (idempotent — safe to call multiple times)
    - Redirects to the workspace
    """
    if request.method == 'POST':
        room_id = request.POST.get('room_id', '').strip()

        if not room_id:
            rooms = Room.objects.filter(members=request.user).order_by('-created_at')
            return render(request, 'dashboard.html', {
                'rooms': rooms,
                'username': request.user.username,
                'join_error': "Please enter a room ID.",
            })

        # Try to find the room — return error if it doesn't exist
        try:
            room = Room.objects.get(room_id=room_id)
        except Room.DoesNotExist:
            rooms = Room.objects.filter(members=request.user).order_by('-created_at')
            return render(request, 'dashboard.html', {
                'rooms': rooms,
                'username': request.user.username,
                'join_error': f"Room '{room_id}' not found. Please check the ID.",
            })

        # Add user to members — .add() is idempotent (won't create duplicates)
        room.members.add(request.user)

        # Redirect to the workspace
        return redirect('workspace', room_id=room_id)

    # GET request — redirect to dashboard
    return redirect('dashboard')


# ─────────────────────────────────────────────────────────────────────────────
# TASK 4.4 — WORKSPACE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def workspace(request, room_id):
    """
    The main meeting workspace page.

    Loads everything the template needs:
      - room          : The Room object
      - is_host       : True if the current user created this room
      - is_recording  : Current recording state (from DB)
      - messages      : Last 50 chat messages (oldest first)
      - note          : The user's saved note for this room (or None)
      - files         : All shared files in this room (newest first)
      - participants  : Placeholder list (live list comes from WebSocket)
      - ZEGO_APP_ID / ZEGO_SERVER_SECRET : Passed to ZegoCloud JS SDK
    """
    # Fetch the room — return 404 if it doesn't exist
    room = get_object_or_404(Room, room_id=room_id)

    # Auto-add user to members if they navigate directly to the URL
    # (handles the rejoin case — idempotent)
    room.members.add(request.user)

    # Determine if the current user is the host
    # This is ALWAYS computed server-side — never trusted from the client
    is_host = (request.user == room.created_by)

    # Load the last 50 messages, oldest first (for correct chat display order)
    # We query newest-first with [:50] then reverse in Python for display order
    messages = list(
        Message.objects.filter(room=room).order_by('-timestamp')[:50]
    )
    messages.reverse()   # Now oldest → newest for display

    # Load the user's note for this room (None if they haven't written one yet)
    note = Note.objects.filter(room=room, author=request.user).first()

    # Load all shared files, newest first
    files = SharedFile.objects.filter(room=room).order_by('-uploaded_at')

    return render(request, 'workspace.html', {
        'room':              room,
        'room_id':           room.room_id,
        'room_name':         room.name,
        'is_host':           is_host,
        'is_recording':      room.is_recording,
        'messages':          messages,
        'note':              note,
        'files':             files,
        'username':          request.user.username,
        'ZEGO_APP_ID':       getattr(settings, 'ZEGO_APP_ID', ''),
        'ZEGO_SERVER_SECRET': getattr(settings, 'ZEGO_SERVER_SECRET', ''),
    })


# ─────────────────────────────────────────────────────────────────────────────
# TASK 5.1 — SAVE NOTE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def save_note(request, room_id):
    """
    Save or update the current user's note for a room.

    Uses update_or_create so there is always exactly one note
    per (user, room) pair — never duplicates.

    Returns JSON: { "status": "saved", "updated_at": "<ISO timestamp>" }
    """
    room = get_object_or_404(Room, room_id=room_id)

    # Only room members can save notes
    if not room.members.filter(pk=request.user.pk).exists():
        return JsonResponse({'error': 'You are not a member of this room.'}, status=403)

    content = request.POST.get('content', '')

    # update_or_create: update if note exists, create if it doesn't
    note, _ = Note.objects.update_or_create(
        room=room,
        author=request.user,
        defaults={'content': content},
    )

    return JsonResponse({
        'status': 'saved',
        'updated_at': note.updated_at.isoformat(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# TASK 5.2 — UPLOAD FILE
# ─────────────────────────────────────────────────────────────────────────────

# Allowed MIME types for file uploads
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB in bytes


@login_required
@require_POST
def upload_file(request, room_id):
    """
    Upload a file to a room.

    Validates:
      - User is a room member
      - File MIME type is in the allowed list
      - File size does not exceed 20 MB

    Returns JSON with file info on success, or error details on failure.
    """
    room = get_object_or_404(Room, room_id=room_id)

    # Only room members can upload files
    if not room.members.filter(pk=request.user.pk).exists():
        return JsonResponse({'error': 'You are not a member of this room.'}, status=403)

    uploaded = request.FILES.get('file')
    if not uploaded:
        return JsonResponse({'error': 'No file provided.'}, status=400)

    # ── Validate MIME type ────────────────────────────────────────────────────
    mime_type = uploaded.content_type
    if mime_type not in ALLOWED_MIME_TYPES:
        return JsonResponse({
            'error': 'invalid_type',
            'message': 'File type not allowed. Accepted: images, PDF, Word, Excel, plain text.',
        }, status=400)

    # ── Validate file size ────────────────────────────────────────────────────
    if uploaded.size > MAX_FILE_SIZE:
        return JsonResponse({
            'error': 'size_exceeded',
            'message': 'File exceeds the 20 MB size limit.',
        }, status=400)

    # ── Save the file ─────────────────────────────────────────────────────────
    shared_file = SharedFile.objects.create(
        room=room,
        uploaded_by=request.user,
        file=uploaded,
        original_filename=uploaded.name,
    )

    # Build the download URL pointing to serve_file view (not raw media path)
    download_url = f"/files/{shared_file.pk}/"

    return JsonResponse({
        'original_filename': shared_file.original_filename,
        'uploaded_by':       request.user.username,
        'uploaded_at':       shared_file.uploaded_at.isoformat(),
        'download_url':      download_url,
        'file_id':           shared_file.pk,
    })


# ─────────────────────────────────────────────────────────────────────────────
# TASK 5.3 — SERVE FILE
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def serve_file(request, file_id):
    """
    Serve an uploaded file — only to authenticated room members.

    Returns 403 if the user is not a member of the room the file belongs to.
    Returns 404 if the file does not exist.
    """
    shared_file = get_object_or_404(SharedFile, pk=file_id)

    # Check the user is a member of the room this file belongs to
    if not shared_file.room.members.filter(pk=request.user.pk).exists():
        return JsonResponse({'error': 'Access denied.'}, status=403)

    # Serve the file as a download
    try:
        response = FileResponse(
            shared_file.file.open('rb'),
            as_attachment=True,
            filename=shared_file.original_filename,
        )
        return response
    except FileNotFoundError:
        raise Http404("File not found on server.")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 5.4 — TOGGLE RECORDING
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def toggle_recording(request, room_id):
    """
    Start or stop recording — host only.
    On stop: creates a placeholder SharedFile entry and broadcasts
    a recording_file event to all clients so it appears in chat.
    """
    room = get_object_or_404(Room, room_id=room_id)

    if request.user != room.created_by:
        return JsonResponse({'error': 'Only the host can control recording.'}, status=403)

    channel_layer = get_channel_layer()
    group_name = f"chat_{room_id}"

    if not room.is_recording:
        # ── Start recording ───────────────────────────────────────────────
        room.is_recording = True
        room.save(update_fields=['is_recording'])

        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'recording_started',
        })
        return JsonResponse({'is_recording': True, 'status': 'started'})

    else:
        # ── Stop recording ────────────────────────────────────────────────
        room.is_recording = False
        room.save(update_fields=['is_recording'])

        # Create a persistent SharedFile entry for the recording.
        # Uses a timestamped filename so multiple recordings per room are stored separately.
        import os
        from django.core.files.base import ContentFile
        from django.utils import timezone

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"meeting_record_{room_id}_{timestamp}.txt"
        placeholder_content = (
            f"Zyncom Meeting Recording\n"
            f"========================\n"
            f"Room:        {room.name} ({room_id})\n"
            f"Recorded by: {request.user.username}\n"
            f"Stopped at:  {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            f"Note: This is a recording placeholder.\n"
            f"Real video capture requires a media server (e.g. Agora Cloud Recording).\n"
        ).encode('utf-8')

        shared_file = SharedFile(
            room=room,
            uploaded_by=request.user,
            original_filename=filename,
        )
        shared_file.file.save(filename, ContentFile(placeholder_content), save=True)

        download_url = f"/files/{shared_file.pk}/"

        # Broadcast recording_stopped + recording_file to all clients
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'recording_stopped',
        })
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'recording_file',
            'filename':    filename,
            'file_url':    download_url,
            'uploaded_by': request.user.username,
            'file_id':     shared_file.pk,
        })

        return JsonResponse({'is_recording': False, 'status': 'stopped', 'file_id': shared_file.pk})


# ─────────────────────────────────────────────────────────────────────────────
# TASK 5.5 — REMOVE PARTICIPANT
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def remove_participant(request, room_id, username):
    """
    Remove a participant from the room — host only.

    - Returns 403 if the user is not the host
    - Broadcasts a force_remove event via WebSocket so the participant's
      browser disconnects and redirects them to the dashboard
    - Removes the user from room.members
    """
    from django.contrib.auth.models import User as AuthUser

    room = get_object_or_404(Room, room_id=room_id)

    # Only the host can remove participants
    if request.user != room.created_by:
        return JsonResponse({'error': 'Only the host can remove participants.'}, status=403)

    # Find the user to remove
    try:
        target_user = AuthUser.objects.get(username=username)
    except AuthUser.DoesNotExist:
        return JsonResponse({'error': f"User '{username}' not found."}, status=404)

    # Cannot remove yourself (the host)
    if target_user == request.user:
        return JsonResponse({'error': 'You cannot remove yourself.'}, status=400)

    # Broadcast force_remove so the participant's WebSocket client redirects them
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f"chat_{room_id}", {
        'type': 'force_remove',
        'target_username': username,
    })

    # Remove from room members
    room.members.remove(target_user)

    return JsonResponse({'status': 'ok', 'removed': username})


# ─────────────────────────────────────────────────────────────────────────────
# TASK 5.6 — END MEETING
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def end_meeting(request, room_id):
    """
    End the meeting for all participants — host only.

    - Returns 403 if the user is not the host
    - Broadcasts end_meeting event via WebSocket — all clients show
      "Meeting ended by host" overlay then redirect to dashboard after 3 seconds
    - The Room record is NOT deleted — it stays on the dashboard and can be re-joined
    - If recording was active, it is stopped automatically
    """
    room = get_object_or_404(Room, room_id=room_id)

    # Only the host can end the meeting
    if request.user != room.created_by:
        return JsonResponse({'error': 'Only the host can end the meeting.'}, status=403)

    # If recording was active, stop it cleanly
    if room.is_recording:
        room.is_recording = False
        room.save(update_fields=['is_recording'])

    # Broadcast end_meeting to all connected clients
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f"chat_{room_id}", {
        'type': 'end_meeting',
    })

    return JsonResponse({'status': 'ok'})
