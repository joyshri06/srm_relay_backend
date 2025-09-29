from django.contrib import admin
from .models import (
    Contact, Group, VoiceMessage, Delivery,
    MessageTemplate, AuditLog, Message, ReplyMessage
)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'user', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('name', 'email', 'phone', 'user__username')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(VoiceMessage)
class VoiceMessageAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'sender_name', 'sender_role', 'target_group',
        'priority', 'status', 'stt_status', 'scheduled_for', 'created_at'
    )
    list_filter = ('priority', 'status', 'stt_status', 'target_group', 'sender_role')
    search_fields = ('sender_name', 'transcribed_text')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'recipient', 'status', 'retries', 'updated_at', 'read_at')
    list_filter = ('status', 'updated_at')
    search_fields = ('recipient_name', 'message_id')


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title', 'body')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('event', 'created_at')
    search_fields = ('event', 'details')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'target_role', 'status', 'created_at',
        'has_text', 'has_audio', 'has_image'
    )
    list_filter = ('status', 'target_role', 'created_at')
    search_fields = ('text', 'user__username')

    def has_text(self, obj):
        return bool(obj.text)
    has_text.boolean = True
    has_text.short_description = "Text?"

    def has_audio(self, obj):
        return bool(obj.audio_url)
    has_audio.boolean = True
    has_audio.short_description = "Audio?"

    def has_image(self, obj):
        return bool(obj.image_url)
    has_image.boolean = True
    has_image.short_description = "Image?"


@admin.register(ReplyMessage)
class ReplyMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'original_message', 'sender', 'created_at')
    search_fields = ('sender__name', 'reply_text')