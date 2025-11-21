from django.contrib import admin
from .models import Incident, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('created_at',)
    can_delete = False

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'link', 'status', 'priority', 'is_escalated', 'created_at')
    list_filter = ('status', 'priority', 'is_escalated')
    search_fields = ('title', 'description')
    inlines = [ChatMessageInline] # See messages attached to this incident

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'link', 'incident', 'created_at', 'is_read')
    list_filter = ('created_at', 'is_read')