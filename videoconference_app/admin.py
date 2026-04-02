"""
Zyncom - Admin Registration
=============================
Registers all four models so they appear in the Django admin panel.
Visit /admin/ to manage rooms, messages, notes, and files.
"""

from django.contrib import admin
from .models import Room, Message, Note, SharedFile


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    # Columns shown in the room list
    list_display = ('name', 'room_id', 'created_by', 'is_recording', 'created_at')
    # Make room_id and name searchable
    search_fields = ('name', 'room_id')
    # Filter sidebar
    list_filter = ('is_recording', 'created_at')
    # Read-only fields (auto-set)
    readonly_fields = ('created_at',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'timestamp', 'content_preview')
    search_fields = ('user__username', 'room__name', 'content')
    list_filter = ('room', 'timestamp')
    readonly_fields = ('timestamp',)

    def content_preview(self, obj):
        """Show first 60 characters of the message in the list view."""
        return obj.content[:60]
    content_preview.short_description = 'Message preview'


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('author', 'room', 'updated_at')
    search_fields = ('author__username', 'room__name')
    list_filter = ('room', 'updated_at')
    readonly_fields = ('updated_at',)


@admin.register(SharedFile)
class SharedFileAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'uploaded_by', 'room', 'uploaded_at')
    search_fields = ('original_filename', 'uploaded_by__username', 'room__name')
    list_filter = ('room', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
