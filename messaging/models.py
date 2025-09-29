from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Contact(models.Model):
    ROLE_CHOICES = [
        ('PRINCIPAL', 'Principal'),
        ('VICE_PRINCIPAL', 'Vice Principal'),
        ('HOD', 'Head of Department'),
        ('STAFF', 'Faculty'),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contact_profiles',
        default=1
    )

    def __str__(self):
        return f"{self.name} ({self.role})"


class Group(models.Model):
    name = models.CharField(max_length=120, unique=True)
    contacts = models.ManyToManyField(Contact, related_name='groups', blank=True)

    def __str__(self):
        return self.name


class VoiceMessage(models.Model):
    PRIORITY_CHOICES = [('NORMAL', 'Normal'), ('URGENT', 'Urgent')]
    SENDING_STATUS = [
        ('QUEUED', 'Queued'),
        ('SENT', 'Sent'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    TARGET_GROUP_CHOICES = [
        ('HOD', 'Head of Department'),
        ('STAFF', 'Faculty'),
        ('BOTH', 'Both HOD and Faculty'),
    ]

    sender_name = models.CharField(max_length=120)
    sender_role = models.CharField(max_length=20, choices=Contact.ROLE_CHOICES, default='VICE_PRINCIPAL')
    target_group = models.CharField(max_length=10, choices=TARGET_GROUP_CHOICES, default='BOTH')
    audio_file = models.FileField(upload_to='audio/', blank=True)
    transcribed_text = models.TextField(blank=True)
    stt_confidence = models.FloatField(null=True, blank=True)
    stt_status = models.CharField(max_length=20, default='PENDING')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='NORMAL')
    scheduled_for = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SENDING_STATUS, default='QUEUED')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        ts = self.created_at.strftime('%Y-%m-%d %H:%M')
        return f"{self.sender_name} → {self.target_group} | {self.priority} | {ts}"


class Delivery(models.Model):
    DELIVERY_STATUS = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('DELIVERED', 'Delivered'),
        ('READ', 'Read'),
        ('FAILED', 'Failed'),
    ]

    message = models.ForeignKey(VoiceMessage, on_delete=models.CASCADE, related_name='deliveries')
    recipient = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='deliveries')
    status = models.CharField(max_length=10, choices=DELIVERY_STATUS, default='PENDING')
    retries = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('message', 'recipient')


class ReplyMessage(models.Model):
    original_message = models.ForeignKey(VoiceMessage, on_delete=models.CASCADE, related_name='replies')
    sender = models.ForeignKey(Contact, on_delete=models.CASCADE)
    reply_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply from {self.sender.name} to message {self.original_message.id}"


class MessageTemplate(models.Model):
    title = models.CharField(max_length=100, unique=True)
    body = models.TextField()

    def __str__(self):
        return self.title
class AuditLog(models.Model):
    event = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        ts = self.created_at.strftime('%Y-%m-%d %H:%M')
        return f"{self.event} @ {ts}"



class Message(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    text = models.TextField(blank=True)
    audio_url = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages_sent',
        default=1
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # Use roles consistent with the rest of your app
    target_role = models.CharField(max_length=50, default='STAFF')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        snippet = self.text[:30] if self.text else ''
        return f"{self.user.username} → {self.target_role}: {snippet}"
