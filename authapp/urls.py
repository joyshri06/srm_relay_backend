from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import google_auth

urlpatterns = [
    path('google/', google_auth, name='google_auth'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
