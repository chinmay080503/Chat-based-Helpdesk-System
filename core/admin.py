from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Ticket, KnowledgeBase, Message

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (('Role', {'fields': ('role', 'bio')}),)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'priority', 'created_by', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority']

@admin.register(KnowledgeBase)
class KBAdmin(admin.ModelAdmin):
    list_display = ['question', 'created_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'is_bot', 'created_at']