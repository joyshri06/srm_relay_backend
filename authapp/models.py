from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('PRINCIPAL', 'Principal'),
        ('VICE_PRINCIPAL', 'Vice Principal'),
        ('HOD', 'Head of Department'),
        ('FACULTY', 'Faculty'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auth_messages')
    text = models.CharField(max_length=255, blank=True)
    audio_url = models.URLField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('approved', 'Approved'),
            ('pending', 'Pending'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )
    target_role = models.CharField(
        max_length=20,
        choices=[
            ('user', 'User'),
            ('official', 'Official'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.target_role} [{self.status}]"
