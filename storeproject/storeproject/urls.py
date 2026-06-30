from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # Default Django admin (optional)
    path('admin/', admin.site.urls),

    # User website
    path('', include('storeapp.urls')),

    # Custom admin panel
    path('admin-panel/', include('adminpanel.urls')),
]

from django.views.static import serve
from django.urls import re_path

# Serve media files (works in both development and production)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]