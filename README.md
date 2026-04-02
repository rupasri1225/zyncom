# Zyncom — Real-Time Collaboration Platform

A Microsoft Teams-style video collaboration platform built with Django and ZegoCloud.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Django](https://img.shields.io/badge/Django-5.1-green)
![Channels](https://img.shields.io/badge/Django%20Channels-4.3-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

- **HD Video Calls** — powered by ZegoCloud WebRTC (camera, mic, screen share)
- **Real-Time Chat** — WebSocket-based messaging with message history
- **Meeting Notes** — per-user notes saved per room, auto-persisted
- **File Sharing** — upload and share images, PDFs, Word, Excel, plain text
- **Meeting Recording** — host-controlled recording saved as a downloadable file
- **Participant Management** — host can remove users and end meetings
- **Role System** — host badge, host-only controls (recording, remove, end meeting)
- **Activity Log** — real-time log of all room events
- **Toast Notifications** — join/leave/file/recording alerts
- **Dashboard** — create/join rooms, search, room cards
- **Zyncom Branding** — purple gradient theme, favicon, footer

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1 |
| WebSockets | Django Channels 4.3 + Daphne |
| Video | ZegoCloud UIKit (WebRTC) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Static files | WhiteNoise |
| Config | python-decouple |
| Frontend | Vanilla JS + Bootstrap 5 |

---

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/zyncom.git
cd zyncom
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ZEGO_APP_ID=your_zego_app_id
ZEGO_SERVER_SECRET=your_zego_server_secret
```

Get ZegoCloud credentials free at [console.zegocloud.com](https://console.zegocloud.com).

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 7. Start the server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000`

---

## Project Structure

```
zyncom/
├── videoconference_app/        # Main Django app
│   ├── migrations/             # Database migrations
│   ├── static/
│   │   ├── css/zyncom.css      # Global design system
│   │   └── img/favicon.svg     # Zyncom favicon
│   ├── templates/              # HTML templates
│   │   ├── base.html           # Base layout (navbar, footer)
│   │   ├── index.html          # Landing page
│   │   ├── login.html          # Login page
│   │   ├── register.html       # Register page
│   │   ├── dashboard.html      # Room management
│   │   └── workspace.html      # Meeting workspace
│   ├── admin.py                # Admin registrations
│   ├── consumers.py            # WebSocket ChatConsumer
│   ├── forms.py                # RegisterForm
│   ├── models.py               # Room, Message, Note, SharedFile
│   ├── routing.py              # WebSocket URL routing
│   ├── urls.py                 # HTTP URL routing
│   └── views.py                # All views
├── videoconferencing/          # Django project config
│   ├── asgi.py                 # ASGI entry point (HTTP + WebSocket)
│   ├── settings.py             # Settings (reads from .env)
│   ├── urls.py                 # Root URL config
│   └── wsgi.py                 # WSGI entry point
├── .env.example                # Environment variable template
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

---

## Deployment on Render

1. Push code to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Set **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
4. Set **Start Command**: `daphne -b 0.0.0.0 -p $PORT videoconferencing.asgi:application`
5. Add environment variables in Render dashboard:
   - `DEBUG=False`
   - `SECRET_KEY=<generate a strong key>`
   - `ZEGO_APP_ID=<your app id>`
   - `ZEGO_SERVER_SECRET=<your secret>`
6. For production WebSockets, switch `CHANNEL_LAYERS` to `channels_redis` and add a Redis instance

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | Yes | `True` for dev, `False` for prod |
| `ZEGO_APP_ID` | Yes | ZegoCloud App ID |
| `ZEGO_SERVER_SECRET` | Yes | ZegoCloud Server Secret |
| `DATABASE_URL` | No | PostgreSQL URL (SQLite used if not set) |
| `EMAIL_HOST_USER` | No | Gmail address for contact form |
| `EMAIL_HOST_PASSWORD` | No | Gmail app password |

---

## Credits

Designed by **Yarramsetti Rupa Sri & Team**
