from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

User = get_user_model()

def get_tokens_for_user(user):
    """Helper to issue JWT tokens with role claim included."""
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.role or None   # ✅ embed role into token
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

@api_view(['POST'])
@permission_classes([AllowAny])  # Public endpoint for Google login
def google_auth(request):
    """
    Authenticate a user via Google OAuth2 ID token.
    If the user does not exist, create them without a role.
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
            settings.GOOGLE_WEB_CLIENT_ID
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
                'is_staff': True,
            }
        )

        # ✅ Issue JWT tokens with role claim
        tokens = get_tokens_for_user(user)

        return Response({
            **tokens,
            'user': {
                'email': user.email,
                'name': user.first_name,
                'picture': picture,
                'role': user.role,  # None if not set yet
            }
        })

    except ValueError:
        return Response({'error': 'Invalid ID token'}, status=400)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def set_role(request):
    """
    Endpoint to set the role for a user after role-selection page.
    Returns updated JWT tokens with role claim.
    """
    try:
        email = request.data.get('email')
        role = request.data.get('role')

        if not email or not role:
            return Response({'error': 'Email and role are required'}, status=400)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User not found'}, status=404)

        user.role = role
        user.save()

        # ✅ Issue new tokens with updated role
        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Role updated successfully',
            'role': user.role,
            **tokens
        })

    except Exception as e:
        return Response({'error': str(e)}, status=500)
