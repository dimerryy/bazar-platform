from django.contrib import admin
from django.utils.html import format_html

from .models import Incident, ChatMessage


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    """Admin interface for Incident model."""
    
    list_display = [
        'incident_id_short', 'title', 'link', 'order', 'status_display', 
        'priority_display', 'is_escalated', 'created_at', 'resolved_at'
    ]
    list_filter = ['status', 'priority', 'is_escalated', 'created_at', 'resolved_at']
    search_fields = [
        'id', 'title', 'description', 
        'link__supplier__name', 'link__consumer__business_name',
        'order__id'
    ]
    autocomplete_fields = ['link', 'order']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Incident Information', {
            'fields': ('id', 'title', 'description')
        }),
        ('Context', {
            'fields': ('link', 'order')
        }),
        ('Workflow', {
            'fields': ('status', 'priority', 'is_escalated', 'resolved_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def incident_id_short(self, obj):
        """Display shortened incident ID."""
        return format_html('<strong>#{}</strong>', str(obj.id)[:8])
    incident_id_short.short_description = 'Incident ID'
    
    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            'OPEN': 'red',
            'IN_PROGRESS': 'orange',
            'RESOLVED': 'green',
            'CLOSED': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def priority_display(self, obj):
        """Display priority with color coding."""
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red'
        }
        color = colors.get(obj.priority, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_display.short_description = 'Priority'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('link', 'link__supplier', 'link__consumer', 'order')


class ChatMessageInline(admin.TabularInline):
    """Inline admin for ChatMessage (read-only for reference)."""
    model = ChatMessage
    extra = 0
    can_delete = False
    fields = ['sender', 'text_preview', 'is_read', 'created_at']
    readonly_fields = ['sender', 'text_preview', 'is_read', 'created_at']
    
    def text_preview(self, obj):
        """Display truncated text."""
        if obj.text:
            preview = obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
            return format_html('<span>{}</span>', preview)
        return format_html('<em>No text</em>')
    text_preview.short_description = 'Text'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for ChatMessage model."""
    
    list_display = [
        'sender', 'link', 'incident', 'text_preview', 'has_attachment', 
        'is_audio', 'is_read', 'created_at'
    ]
    list_filter = ['is_read', 'is_audio', 'incident', 'created_at']
    search_fields = [
        'text', 'sender__username', 'sender__email',
        'link__supplier__name', 'link__consumer__business_name',
        'incident__title'
    ]
    autocomplete_fields = ['link', 'sender', 'incident']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Message Information', {
            'fields': ('id', 'link', 'sender', 'incident')
        }),
        ('Content', {
            'fields': ('text', 'attachment', 'is_audio')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def text_preview(self, obj):
        """Display truncated text."""
        if obj.text:
            preview = obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
            return format_html('<span>{}</span>', preview)
        return format_html('<em>No text</em>')
    text_preview.short_description = 'Text'
    
    def has_attachment(self, obj):
        """Display if message has attachment."""
        if obj.attachment:
            return format_html(
                '<span style="color: green;">✓ Yes</span><br>'
                '<a href="{}" target="_blank">View</a>',
                obj.attachment.url
            )
        return format_html('<span style="color: gray;">No</span>')
    has_attachment.short_description = 'Attachment'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('link', 'link__supplier', 'link__consumer', 'sender', 'incident')

