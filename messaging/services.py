from datetime import datetime
from django.utils import timezone
from .models import VoiceMessage, Delivery, Contact, Group, AuditLog

# Simple stub STT: returns placeholder text and confidence.
# You can replace with real STT integration later.
def transcribe_audio(file_path: str):
    # TODO: integrate your preferred STT (e.g., cloud API or local model)
    # For now, simulate a success with moderate confidence:
    text = "Transcription pending review. We've got you covered."
    confidence = 0.65
    return text, confidence

def should_send_now(vm: VoiceMessage) -> bool:
    if not vm.scheduled_for:
        return True
    return timezone.now() >= vm.scheduled_for

def create_deliveries_for_groups(vm: VoiceMessage, group_ids: list[int]):
    recipients = Contact.objects.filter(groups_id_in=group_ids, is_active=True).distinct()
    count = 0
    for r in recipients:
        Delivery.objects.get_or_create(message=vm, recipient=r)
        count += 1
    AuditLog.objects.create(event='DELIVERY_CREATED', details=f'Created {count} deliveries for message {vm.id}')

def attempt_send_deliveries(vm: VoiceMessage, max_retries=3):
    # Simulate delivery sending; in real setup, push notifications or in-app pull.
    for d in vm.deliveries.all():
        if d.status in ('DELIVERED', 'READ'):
            continue
        try:
            # Simulate success for now:
            d.status = 'DELIVERED'
            d.last_error = ''
            d.save()
        except Exception as e:
            d.retries += 1
            d.last_error = str(e)
            d.status = 'FAILED' if d.retries >= max_retries else 'PENDING'
            d.save()
    statuses = vm.deliveries.values_list('status', flat=True)
    if all(s in ('DELIVERED', 'READ') for s in statuses):
        vm.status = 'COMPLETED'
    elif any(s == 'FAILED' for s in statuses):
        vm.status = 'FAILED'
    else:
        vm.status = 'SENT'
    vm.save(update_fields=['status'])
    AuditLog.objects.create(event='DELIVERY_ATTEMPTED', details=f'Message {vm.id} status now {vm.status}')