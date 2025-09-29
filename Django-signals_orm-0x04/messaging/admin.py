from django.contrib import admin
from .models import Message, Notification


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interface for Message model.
    """
    list_display = (
        'id',
        'sender',
        'receiver',
        'content_preview',
        'timestamp',
        'is_read'
    )
    list_filter = (
        'is_read',
        'timestamp',
        'sender',
        'receiver'
    )
    search_fields = (
        'sender__username',
        'receiver__username',
        'content'
    )
    readonly_fields = (
        'timestamp',
    )
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Message Details', {
            'fields': ('sender', 'receiver', 'content')
        }),
        ('Status', {
            'fields': ('is_read', 'timestamp')
        }),
    )

    def content_preview(self, obj):
        """Show a preview of the message content."""
        return f"{obj.content[:50]}{'...' if len(obj.content) > 50 else ''}"
    content_preview.short_description = 'Content Preview'

    def has_add_permission(self, request):
        """Allow adding messages through admin."""
        return True

    def save_model(self, request, obj, form, change):
        """
        Override save to demonstrate that signals work even when
        saving through admin interface.
        """
        super().save_model(request, obj, form, change)
        if not change:  # If creating new message
            self.message_user(
                request,
                f"Message sent and notification created for {obj.receiver.username}"
            )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    """
    list_display = (
        'id',
        'user',
        'notification_type',
        'content_preview',
        'timestamp',
        'is_read',
        'related_message'
    )
    list_filter = (
        'is_read',
        'notification_type',
        'timestamp',
        'user'
    )
    search_fields = (
        'user__username',
        'content',
    )
    readonly_fields = (
        'timestamp',
    )
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'notification_type', 'content', 'message')
        }),
        ('Status', {
            'fields': ('is_read', 'timestamp')
        }),
    )

    def content_preview(self, obj):
        """Show a preview of the notification content."""
        return f"{obj.content[:50]}{'...' if len(obj.content) > 50 else ''}"
    content_preview.short_description = 'Content Preview'

    def related_message(self, obj):
        """Show the related message if exists."""
        if obj.message:
            return f"Message #{obj.message.id}"
        return "No related message"
    related_message.short_description = 'Related Message'

    actions = ['mark_as_read', 'mark_as_unread']

    def mark_as_read(self, request, queryset):
        """Admin action to mark notifications as read."""
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notification(s) marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        """Admin action to mark notifications as unread."""
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notification(s) marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"