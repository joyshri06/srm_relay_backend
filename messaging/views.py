from datetime import timedelta
import json

from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import TruncDate
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, parser_classes

from .models import Contact, Group, VoiceMessage, Delivery, MessageTemplate, Message, ReplyMessage
from .serializers import (
    ContactSerializer, GroupSerializer, VoiceMessageSerializer,
    DeliverySerializer, MessageTemplateSerializer, MessageSerializer
)
from .services import transcribe_audio, create_deliveries_for_groups, attempt_send_deliveries, should_send_now

User = get_user_model()

# Allowed groups consistent with app-wide roles
ALLOWED_GROUPS = {'STAFF', 'HOD', 'VICE_PRINCIPAL', 'PRINCIPAL', 'ALL'}


def has_role(user, allowed_roles):
    return getattr(user, 'role', None) in allowed_roles


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()

        total_users = User.objects.count()
        total_messages = Message.objects.count()
        messages_today = Message.objects.filter(created_at__date=today).count()
        active_users_today = User.objects.filter(last_login__date=today).count()
        messages_per_user = list(Message.objects.values("user__username").annotate(total=Count("id")))
        messages_last_7_days = list(
            Message.objects.filter(created_at__gte=today - timedelta(days=7))
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Count("id"))
            .order_by("day")
        )

        return Response({
            "total_users": total_users,
            "total_messages": total_messages,
            "messages_today": messages_today,
            "active_users_today": active_users_today,
            "messages_per_user": messages_per_user,
            "messages_last_7_days": messages_last_7_days,
        })


@csrf_exempt
def pending_messages(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    if not request.user.email.endswith('@srm.edu.in'):
        return JsonResponse({'error': 'Access denied'}, status=403)

    if request.method == 'GET':
        pending = Message.objects.filter(status='pending').order_by('-created_at')
        data = [
            {
                'id': m.id,
                'text': m.text,
                'audio_url': m.audio_url,
                'image_url': m.image_url,
                'created_at': m.created_at
            }
            for m in pending
        ]
        return JsonResponse(data, safe=False)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            msg_id = body.get('id')
            action = body.get('action')

            msg = Message.objects.get(id=msg_id)
            msg.status = 'approved' if action == 'approve' else 'rejected'
            msg.save()
            return JsonResponse({'success': True})
        except Message.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ContactsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Contact.objects.filter(is_active=True).order_by('name')
        return Response(ContactSerializer(qs, many=True).data)


class GroupsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Group.objects.all().order_by('name')
        return Response(GroupSerializer(qs, many=True).data)


class TemplatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = MessageTemplate.objects.all().order_by('title')
        return Response(MessageTemplateSerializer(qs, many=True).data)


class VoiceMessageView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = VoiceMessage.objects.order_by('-created_at')[:20]
        return Response(VoiceMessageSerializer(qs, many=True).data)

    def post(self, request):
        if not has_role(request.user, ['PRINCIPAL', 'VICE_PRINCIPAL']):
            return Response({'error': 'Permission denied'}, status=403)
        if 'audio_file' not in request.FILES:
            return Response({'error': 'No audio file provided'}, status=400)

        audio_file = request.FILES['audio_file']
        saved_audio = default_storage.save(f'audio/{audio_file.name}', ContentFile(audio_file.read()))

        vm = VoiceMessage.objects.create(
            sender_name=request.user.username,
            sender_role=request.data.get('sender_role', getattr(request.user, 'role', 'VICE_PRINCIPAL')),
            target_group=request.data.get('target_group', 'BOTH'),
            audio_file=saved_audio,
            status='QUEUED'
        )
        return Response({'id': vm.id, 'status': vm.status}, status=201)


class DeliveriesForMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id):
        vm = get_object_or_404(VoiceMessage, pk=message_id)
        d = vm.deliveries.select_related('recipient').all()
        return Response(DeliverySerializer(d, many=True).data)


class AckDeliveryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, delivery_id):
        d = get_object_or_404(Delivery, pk=delivery_id)
        d.status = 'READ'
        d.read_at = timezone.now()
        d.save()
        return Response({"status": "ok", "message": "Acknowledged"})


class RunSchedulerNowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        due = VoiceMessage.objects.filter(status='QUEUED')
        sent = 0
        for vm in due:
            if should_send_now(vm):
                attempt_send_deliveries(vm)
                sent += 1
        return Response({"processed": sent})


# ---------------- Inbox (primary) ----------------
class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Prefer query param role; fallback to user's role; include ALL
        role = request.query_params.get('role') or getattr(request.user, 'role', 'STAFF')
        if role not in ALLOWED_GROUPS:
            role = 'STAFF'

        qs = Message.objects.filter(
            status='approved',
            target_role__in=[role, 'ALL']
        ).order_by('-created_at')

        serializer = MessageSerializer(qs, many=True, context={'request': request})
        # Return keys: id, text, audio_url, image_url, from_field, target_role, created_at
        return Response(serializer.data)


# ---------------- Emergency (public) ----------------
class EmergencyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "status": "ok",
            "message": "Emergency endpoint active."
        })


class AudioUploadView(APIView):
    parser_classes = [MultiPartParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not has_role(request.user, ['PRINCIPAL', 'VICE_PRINCIPAL']):
            return Response({'error': 'Permission denied'}, status=403)
        if 'audio' not in request.FILES:
            return Response({'error': 'No audio file provided'}, status=400)

        audio_file = request.FILES['audio']
        file_path = default_storage.save(f'audio/{audio_file.name}', ContentFile(audio_file.read()))
        file_url = default_storage.url(file_path)

        target_group = request.data.get('target_group', 'ALL')
        if target_group not in ALLOWED_GROUPS:
            return Response({'error': 'Invalid target_group', 'allowed_groups': sorted(ALLOWED_GROUPS)}, status=400)

        msg = Message.objects.create(
            text="Recorded message",
            audio_url=file_url,
            user=request.user,
            status='approved',
            target_role=target_group
        )

        return Response({
            'message': 'Audio uploaded and message created',
            'url': file_url,
            'message_id': msg.id
        }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def send_message(request):
    if not has_role(request.user, ['PRINCIPAL', 'VICE_PRINCIPAL']):
        return Response({'error': 'Permission denied'}, status=403)

    text = (request.data.get('message_text') or '').strip()
    target_group = (request.data.get('target_group') or '').strip()
    audio_file = request.FILES.get('audio')
    image_file = request.FILES.get('image')

    if not target_group or target_group not in ALLOWED_GROUPS:
        return Response({'error': 'Invalid or missing target_group', 'allowed_groups': sorted(ALLOWED_GROUPS)}, status=400)

    if not text and not audio_file and not image_file:
        return Response({'error': 'Message text, audio, or image is required'}, status=400)

    audio_url = None
    image_url = None

    if audio_file:
        saved_audio = default_storage.save(f'audio/{audio_file.name}', ContentFile(audio_file.read()))
        audio_url = default_storage.url(saved_audio)

    if image_file:
        saved_image = default_storage.save(f'images/{image_file.name}', ContentFile(image_file.read()))
        image_url = default_storage.url(saved_image)

    msg = Message.objects.create(
        text=text if text else "Media message",
        audio_url=audio_url,
        image_url=image_url,
        user=request.user,
        status='approved',
        target_role=target_group
    )

    return Response({
        'success': True,
        'message_id': msg.id,
        'text': msg.text,
        'target_group': target_group,
        'audio_url': audio_url,
        'image_url': image_url,
        'created_at': msg.created_at
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_reply(request):
    if not has_role(request.user, ['HOD', 'STAFF']):
        return Response({'error': 'Permission denied'}, status=403)

    message_id = request.data.get('message_id')
    reply_text = (request.data.get('reply_text') or '').strip()

    if not reply_text:
        return Response({'error': 'Reply text is required'}, status=400)

    try:
        original = Message.objects.get(id=message_id)
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=404)

    ReplyMessage.objects.create(
        original_message=original,
        sender=Contact.objects.filter(user=request.user).first(),
        reply_text=reply_text
    )

    return Response({'success': True})


# ---------------- Inbox test (kept for quick debugging) ----------------
class InboxView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Message.objects.filter(
            target_role__in=['STAFF', 'ALL'],
            status='approved'
        ).order_by('-created_at')[:10]

        serializer = MessageSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)
