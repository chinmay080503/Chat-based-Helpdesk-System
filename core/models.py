from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [('admin', 'Admin'), ('agent', 'Agent'), ('user', 'User')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class KnowledgeBase(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    keywords = models.CharField(max_length=300, blank=True, help_text="Comma-separated keywords")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question


class Ticket(models.Model):
    STATUS = [('open','Open'),('in_progress','In Progress'),('resolved','Resolved'),('closed','Closed')]
    PRIORITY = [('low','Low'),('medium','Medium'),('high','High'),('urgent','Urgent')]

    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='open')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class Message(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_bot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']