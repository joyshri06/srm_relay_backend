from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from authapp.views import google_auth  # ✅ Import Google login view

urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Messaging app endpoints
    path('api/messages/', include('messaging.urls')),

    # Auth app endpoints
    path('api/auth/google/', google_auth, name='google_auth'),  # ✅ Google login
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)