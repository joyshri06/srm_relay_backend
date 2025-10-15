from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import google_auth, firebase_auth, set_role

urlpatterns = [
    path('google/', google_auth, name='google_auth'),
    path('firebase/', firebase_auth, name='firebase_auth'),
    path('set-role/', set_role, name='set_role'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
