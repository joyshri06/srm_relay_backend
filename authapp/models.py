from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('PRINCIPAL', 'Principal'),
        ('VICE_PRINCIPAL', 'Vice Principal'),
        ('HOD', 'Head of Department'),
        ('FACULTY', 'Faculty'),
        ('STAFF', 'Staff'),  # ✅ Added to match your Flutter RoleSelectionScreen
    ]

    role = models.CharField(
        "User Role",
        max_length=20,
        choices=ROLE_CHOICES,
        null=True,        # allow empty in DB
        blank=True,       # allow empty in forms
        default=None
    )

    def __str__(self):
        return f"{self.username} ({self.role or 'No Role'})"


class Message(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='auth_messages'
    )
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
        choices=User.ROLE_CHOICES,  # ✅ Reuse same role choices for targeting
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # ✅ newest first

    def __str__(self):
        return f"{self.user.username} → {self.target_role or 'N/A'} [{self.status}]"
