"""
URL configuration for Smart_Analitics project.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('welcome.urls')),
    path('main/', include('main.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# In development mode (DEBUG=True) Django will serve media files
# (uploaded avatars, datasets) via the built-in server.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
