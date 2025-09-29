from django.urls import path
from .views import (
    # Stats and approval
    pending_messages,
    AdminStatsView,

    # Core data
    ContactsView,
    GroupsView,
    TemplatesView,

    # Voice messages and deliveries
    VoiceMessageView,
    DeliveriesForMessageView,
    AckDeliveryView,

    # Scheduler
    RunSchedulerNowView,

    # Inbox and public
    MessageListView,
    InboxView,

    # Emergency
    EmergencyView,

    # Media
    AudioUploadView,

    # Messaging actions
    send_message,
    send_reply,
)

urlpatterns = [
    # 📊 Stats and approvals
    path('admin-stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('pending/', pending_messages, name='pending_messages'),

    # 📂 Core data
    path('contacts/', ContactsView.as_view(), name='contacts'),
    path('groups/', GroupsView.as_view(), name='groups'),
    path('templates/', TemplatesView.as_view(), name='templates'),

    # 🎙 Voice messages and deliveries
    path('voice/', VoiceMessageView.as_view(), name='voice_messages'),
    path('voice/<int:message_id>/deliveries/', DeliveriesForMessageView.as_view(), name='deliveries_for_message'),
    path('deliveries/<int:delivery_id>/ack/', AckDeliveryView.as_view(), name='ack_delivery'),

    # ⏱ Scheduler
    path('scheduler/run/', RunSchedulerNowView.as_view(), name='run_scheduler_now'),

    # 📥 Inbox and public
    path('inbox-test/', InboxView.as_view(), name='inbox_test'),
    path('inbox/', MessageListView.as_view(), name='inbox'),

    # 🚨 Emergency
    path('emergency/', EmergencyView.as_view(), name='emergency'),

    # 📎 Media
    path('audio/upload/', AudioUploadView.as_view(), name='audio_upload'),

    # 💬 Messaging actions
    path('send/', send_message, name='send_message'),
    path('reply/', send_reply, name='send_reply'),
]