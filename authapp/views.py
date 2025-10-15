from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests as py_requests  # for Firebase token verification

User = get_user_model()


def get_tokens_for_user(user):
    """Helper to issue JWT tokens with role claim included."""
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role or None
    access = refresh.access_token
    access['role'] = user.role or None
    return {
        'access': str(access),
        'refresh': str(refresh),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """Authenticate a user via Google OAuth2 ID token."""
    try:
        token = request.data.get('id_token')
        if not token:
            return Response({'error': 'Missing ID token'}, status=400)

        idinfo = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_WEB_CLIENT_ID
        )

        email = idinfo.get('email')
        name = idinfo.get('name')
        picture = idinfo.get('picture')

        if not email:
            return Response({'error': 'Email not found in token'}, status=400)

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'first_name': name or '',
                'email': email,
                'is_active': True,
                'is_staff': False,
                'role': None,
            }
        )

        tokens = get_tokens_for_user(user)

        return Response({
            **tokens,
            'user': {
                'email': user.email,
                'name': user.first_name,
                'picture': picture,
                'role': user.role,
            }
        })

    except ValueError:
        return Response({'error': 'Invalid ID token'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def firebase_auth(request):
    """
    Authenticate a user via Firebase ID token (email/password flow).
    If the user does not exist, create them without a role.
    """
    try:
        token = request.data.get('id_token')
        email = request.data.get('email')
        if not token or not email:
            return Response({'error': 'ID token and email are required'}, status=400)

        # Verify Firebase ID token with Google
        verify_url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={settings.FIREBASE_API_KEY}"
        resp = py_requests.post(verify_url, json={"idToken": token})
        if resp.status_code != 200:
            return Response({'error': 'Invalid Firebase ID token'}, status=400)

        data = resp.json()
        users = data.get("users", [])
        if not users:
            return Response({'error': 'No user found for this token'}, status=400)

        name = users[0].get("displayName", "")
        picture = users[0].get("photoUrl", "")

        # Create or get Django user
        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'first_name': name or '',
                'email': email,
                'is_active': True,
                'is_staff': False,
                'role': None,
            }
        )

        tokens = get_tokens_for_user(user)

        return Response({
            **tokens,
            'user': {
                'email': user.email,
                'name': user.first_name,
                'picture': picture,
                'role': user.role,
            }
        })

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_role(request):
    """Set the role for the authenticated user."""
    try:
        role = request.data.get('role')
        if not role:
            return Response({'error': 'Role is required'}, status=400)

        user = request.user
        user.role = role
        user.save()

        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Role updated successfully',
            'role': user.role,
            **tokens
        })

    except Exception as e:
        return Response({'error': str(e)}, status=500)
