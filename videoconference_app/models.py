"""
Zyncom - Data Models
=====================
Defines the four core database models for the platform:
  - Room        : A persistent meeting workspace
  - Message     : A chat message inside a room
  - Note        : A user's personal notes inside a room
  - SharedFile  : A file uploaded and shared inside a room
"""

from django.db import models
from django.contrib.auth.models import User


# ─────────────────────────────────────────────────────────────────────────────
# ROOM
# ─────────────────────────────────────────────────────────────────────────────

class Room(models.Model):
    """
    A persistent meeting workspace.

    - room_id      : Short unique slug used in URLs (e.g. "a3f9b2c1")
    - name         : Human-readable room name shown in the UI
    - created_by   : The user who created the room — this is the HOST
    - members      : All users who have joined this room (many-to-many)
    - is_recording : Whether the room is currently being recorded
    - created_at   : When the room was created (set automatically)
    """

    room_id = models.SlugField(
        max_length=20,
        unique=True,
        help_text="Short unique identifier used in the room URL"
    )
    name = models.CharField(
        max_length=200,
        help_text="Display name for the room"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_rooms',
        help_text="The user who created this room (the host)"
    )
    members = models.ManyToManyField(
        User,
        related_name='joined_rooms',
        blank=True,
        help_text="All users who have joined this room"
    )
    is_recording = models.BooleanField(
        default=False,
        help_text="True while the host is recording the meeting"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the room was created"
    )

    class Meta:
        ordering = ['-created_at']   # Newest rooms first

    def __str__(self):
        return f"{self.name} ({self.room_id})"


# ─────────────────────────────────────────────────────────────────────────────
# MESSAGE
# ─────────────────────────────────────────────────────────────────────────────

class Message(models.Model):
    """
    A single chat message sent inside a room.

    - room      : Which room this message belongs to
    - user      : Who sent the message (SET_NULL so messages survive if user is deleted)
    - content   : The text of the message
    - timestamp : When the message was sent (set automatically)
    """

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="The room this message was sent in"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='messages',
        help_text="The user who sent this message"
    )
    content = models.TextField(
        help_text="The text content of the message"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the message was sent"
    )

    class Meta:
        ordering = ['timestamp']   # Oldest messages first (chat order)

    def __str__(self):
        username = self.user.username if self.user else "deleted user"
        preview = self.content[:40]
        return f"{username} @ {self.timestamp:%Y-%m-%d %H:%M}: {preview}"


# ─────────────────────────────────────────────────────────────────────────────
# NOTE
# ─────────────────────────────────────────────────────────────────────────────

class Note(models.Model):
    """
    A user's personal meeting notes inside a room.

    Each user gets exactly ONE note per room (enforced by unique_together).
    Saving always does an upsert — create if missing, update if exists.

    - room       : Which room these notes belong to
    - author     : Which user wrote these notes
    - content    : The note text (can be empty — allows clearing notes)
    - updated_at : Last save time (updated automatically on every save)
    """

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='notes',
        help_text="The room these notes belong to"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notes',
        help_text="The user who wrote these notes"
    )
    content = models.TextField(
        blank=True,
        help_text="The note content (blank is allowed)"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time this note was saved"
    )

    class Meta:
        # One note per user per room — enforced at the database level
        unique_together = [('room', 'author')]

    def __str__(self):
        return f"Note by {self.author.username} in '{self.room.name}'"


# ─────────────────────────────────────────────────────────────────────────────
# SHARED FILE
# ─────────────────────────────────────────────────────────────────────────────

class SharedFile(models.Model):
    """
    A file uploaded and shared inside a room.

    Files are stored in MEDIA_ROOT/room_files/.
    Access is restricted to authenticated room members (enforced in views).

    - room              : Which room this file was shared in
    - uploaded_by       : Who uploaded the file (SET_NULL so files survive if user deleted)
    - file              : The actual file stored on disk
    - original_filename : The original name the user gave the file
    - uploaded_at       : When the file was uploaded (set automatically)
    """

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='files',
        help_text="The room this file was shared in"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_files',
        help_text="The user who uploaded this file"
    )
    file = models.FileField(
        upload_to='room_files/',
        help_text="The uploaded file (stored in media/room_files/)"
    )
    original_filename = models.CharField(
        max_length=255,
        help_text="The original filename as uploaded by the user"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the file was uploaded"
    )

    class Meta:
        ordering = ['-uploaded_at']   # Newest files first

    def __str__(self):
        uploader = self.uploaded_by.username if self.uploaded_by else "deleted user"
        return f"{self.original_filename} (by {uploader} in '{self.room.name}')"
