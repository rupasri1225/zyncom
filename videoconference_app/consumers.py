"""
Zyncom - ChatConsumer (WebSocket)
===================================
Handles ALL real-time communication for a room over a single WebSocket
connection per user.

How it works:
  1. User opens the workspace page → browser connects to ws/room/<room_id>/
  2. connect()     → user joins the channel group, others are notified
  3. receive()     → user sends a message → saved to DB, broadcast to group
  4. disconnect()  → user leaves → others are notified, channel removed from group

Event types (server → client JSON):
  chat_message      — a new chat message
  user_joined       — someone connected
  user_left         — someone disconnected
  force_remove      — you have been removed by the host
  end_meeting       — host ended the meeting
  recording_started — recording is now active
  recording_stopped — recording has stopped

Class variable `room_participants`:
  A dict mapping room_id → set of usernames currently connected.
  This is in-memory only — it resets on server restart.
  The DB-persisted is_recording field handles state that must survive restarts.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    """
    Single WebSocket consumer for all real-time room events.
    One instance is created per connected user per room.
    """

    # ── Class-level participant tracking ──────────────────────────────────────
    # Shared across all instances: { room_id: set(username, ...) }
    # Lets us know who is currently online in each room.
    room_participants: dict = {}

    # ─────────────────────────────────────────────────────────────────────────
    # CONNECT
    # ─────────────────────────────────────────────────────────────────────────

    async def connect(self):
        """
        Called when a browser opens a WebSocket connection.

        Steps:
          1. Reject unauthenticated users (close with code 4001)
          2. Read room_id from the URL
          3. Add this channel to the room's group
          4. Track the user in room_participants
          5. Accept the connection
          6. Broadcast user_joined to everyone in the room
          7. Send the current participant list to the newly joined user
        """
        user = self.scope["user"]

        # Step 1 — reject if not logged in
        if not user.is_authenticated:
            await self.close(code=4001)
            return

        # Step 2 — get room_id from URL (ws/room/<room_id>/)
        self.room_id   = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"chat_{self.room_id}"
        self.username   = user.username

        # Step 3 — join the channel group for this room
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        # Step 4 — add to in-memory participant set
        if self.room_id not in ChatConsumer.room_participants:
            ChatConsumer.room_participants[self.room_id] = set()
        ChatConsumer.room_participants[self.room_id].add(self.username)

        # Step 5 — accept the WebSocket connection
        await self.accept()

        # Step 6 — tell everyone else this user joined
        await self.channel_layer.group_send(self.group_name, {
            "type":         "user_joined",
            "username":     self.username,
            "participants": list(ChatConsumer.room_participants[self.room_id]),
        })

    # ─────────────────────────────────────────────────────────────────────────
    # DISCONNECT
    # ─────────────────────────────────────────────────────────────────────────

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection closes (for any reason).

        Steps:
          1. Remove user from in-memory participant set
          2. Broadcast user_left to remaining participants
          3. Remove channel from the group
        """
        # Step 1 — remove from participant tracking
        if self.room_id in ChatConsumer.room_participants:
            ChatConsumer.room_participants[self.room_id].discard(self.username)
            # Clean up empty rooms
            if not ChatConsumer.room_participants[self.room_id]:
                del ChatConsumer.room_participants[self.room_id]

        # Step 2 — notify remaining participants
        try:
            await self.channel_layer.group_send(self.group_name, {
                "type":         "user_left",
                "username":     self.username,
                "participants": list(
                    ChatConsumer.room_participants.get(self.room_id, set())
                ),
            })
        except Exception:
            pass  # Don't crash if channel layer has issues during disconnect

        # Step 3 — leave the group
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # RECEIVE — messages FROM the browser
    # ─────────────────────────────────────────────────────────────────────────

    async def receive(self, text_data):
        """
        Called when the browser sends a message over the WebSocket.

        Expected JSON format:
          { "type": "chat_message", "message": "Hello!" }

        Supported types:
          chat_message — save to DB and broadcast to room
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return  # Ignore malformed messages

        msg_type = data.get("type")

        if msg_type == "chat_message":
            message_text = data.get("message", "").strip()
            if not message_text:
                return  # Ignore empty messages

            # Save message to database (database_sync_to_async wraps the ORM call)
            timestamp = await self._save_message(message_text)

            # Broadcast to everyone in the room (including sender)
            await self.channel_layer.group_send(self.group_name, {
                "type":      "chat_message",
                "username":  self.username,
                "message":   message_text,
                "timestamp": timestamp,
            })

    # ─────────────────────────────────────────────────────────────────────────
    # GROUP SEND HANDLERS — messages FROM the channel layer TO the browser
    # Each method name matches the "type" field in group_send calls.
    # Django Channels routes them automatically (dots replaced with underscores).
    # ─────────────────────────────────────────────────────────────────────────

    async def chat_message(self, event):
        """Forward a chat message to this user's WebSocket."""
        await self.send(text_data=json.dumps({
            "type":      "chat_message",
            "username":  event["username"],
            "message":   event["message"],
            "timestamp": event["timestamp"],
        }))

    async def user_joined(self, event):
        """Tell this client that someone joined the room."""
        await self.send(text_data=json.dumps({
            "type":         "user_joined",
            "username":     event["username"],
            "participants": event["participants"],
        }))

    async def user_left(self, event):
        """Tell this client that someone left the room."""
        await self.send(text_data=json.dumps({
            "type":         "user_left",
            "username":     event["username"],
            "participants": event["participants"],
        }))

    async def force_remove(self, event):
        """
        Tell a specific user they have been removed by the host.
        Only the targeted user's client acts on this — others ignore it.
        The frontend will show a message and redirect to dashboard.
        """
        # Only send the disconnect signal to the targeted user
        if event.get("target_username") == self.username:
            await self.send(text_data=json.dumps({
                "type": "force_remove",
            }))
            # Close this user's WebSocket connection
            await self.close()

    async def end_meeting(self, event):
        """
        Tell all clients the meeting has ended.
        The frontend shows "Meeting ended by host" overlay,
        waits 3 seconds, then redirects to dashboard.
        """
        await self.send(text_data=json.dumps({
            "type": "end_meeting",
        }))
        # Close the WebSocket connection gracefully
        await self.close()

    async def recording_started(self, event):
        """Tell all clients that recording has started."""
        await self.send(text_data=json.dumps({
            "type": "recording_started",
        }))

    async def recording_stopped(self, event):
        """Tell all clients that recording has stopped."""
        await self.send(text_data=json.dumps({
            "type": "recording_stopped",
        }))

    async def recording_file(self, event):
        """Tell all clients a recording file is available — appears in chat."""
        await self.send(text_data=json.dumps({
            "type":        "recording_file",
            "filename":    event["filename"],
            "file_url":    event["file_url"],
            "uploaded_by": event["uploaded_by"],
        }))

    # ─────────────────────────────────────────────────────────────────────────
    # DATABASE HELPER
    # ─────────────────────────────────────────────────────────────────────────

    @database_sync_to_async
    def _save_message(self, content):
        """
        Save a chat message to the database.

        database_sync_to_async is required because Django ORM calls are
        synchronous but ChatConsumer runs in an async context.

        Returns the timestamp as an ISO string for broadcasting.
        """
        from .models import Room, Message

        try:
            room = Room.objects.get(room_id=self.room_id)
            user = self.scope["user"]
            msg  = Message.objects.create(room=room, user=user, content=content)
            return msg.timestamp.isoformat()
        except Exception:
            # If DB save fails, return current time so broadcast still works
            from django.utils import timezone
            return timezone.now().isoformat()
