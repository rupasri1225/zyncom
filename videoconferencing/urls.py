"""
Zyncom - Root URL Configuration
=================================
All app URLs are delegated to videoconference_app/urls.py.
Media files (uploaded files) are served locally in DEBUG mode.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('videoconference_app.urls')),
]

# Serve uploaded media files during development (DEBUG=True).
# In production, a web server (nginx/S3) should serve these instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
