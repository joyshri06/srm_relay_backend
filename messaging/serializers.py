from rest_framework import serializers
from .models import Contact, Group, VoiceMessage, Delivery, MessageTemplate, Message


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'phone', 'role', 'is_active']


class GroupSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'contacts']


class VoiceMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceMessage
        fields = [
            'id', 'sender_name', 'audio_file', 'transcribed_text',
            'stt_confidence', 'stt_status', 'priority', 'scheduled_for',
            'status', 'created_at'
        ]
        read_only_fields = ['transcribed_text', 'stt_confidence', 'stt_status', 'status', 'created_at']


class DeliverySerializer(serializers.ModelSerializer):
    recipient = ContactSerializer(read_only=True)

    class Meta:
        model = Delivery
        fields = ['id', 'recipient', 'status', 'retries', 'last_error', 'updated_at', 'read_at']


class MessageTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageTemplate
        fields = ['id', 'title', 'body']


class MessageSerializer(serializers.ModelSerializer):
    # Use "from" to match frontend; compute from user’s name/username
    from_field = serializers.SerializerMethodField(source='from')
    audio_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'text', 'audio_url', 'image_url', 'from_field', 'target_role', 'created_at']

    def get_from_field(self, obj):
        return obj.user.first_name or obj.user.username

    def _absolute_url(self, url: str):
        if not url:
            return ""
        request = self.context.get('request')
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url

    def get_audio_url(self, obj):
        return self._absolute_url(obj.audio_url or "")

    def get_image_url(self, obj):
        return self._absolute_url(obj.image_url or "")
