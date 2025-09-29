from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])  # Public endpoint for Google login
def google_auth(request):
    """
    Authenticate a user via Google OAuth2 ID token.
    If the user does not exist, create them with a default role.
    Returns JWT access/refresh tokens and basic user info.
    """
    try:
        token = request.data.get('id_token')
        if not token:
            return Response({'error': 'Missing ID token'}, status=400)

        # ✅ Verify token with Google and enforce audience (Web Client ID)
        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_WEB_CLIENT_ID  # must match Flutter's serverClientId
        )

        email = idinfo.get('email')
        name = idinfo.get('name')
        picture = idinfo.get('picture')

        if not email:
            return Response({'error': 'Email not found in token'}, status=400)

        # ✅ Create or get Django user
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'first_name': name or '',
                'email': email,
                'is_active': True,
                'is_staff': True,  # adjust if only certain users should access admin
            }
        )

        # ✅ Ensure user has a role field (if your custom User model supports it)
        if hasattr(user, 'role') and not user.role:
            user.role = 'STAFF'   # default role
            user.save()

        # ✅ Issue JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'email': user.email,
                'name': user.first_name,
                'picture': picture,
                'role': getattr(user, 'role', None),
            }
        })

    except ValueError:
        # Token verification failed
        return Response({'error': 'Invalid ID token'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)