from django.db import admin
from .models import Message, Notification

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interfacee for the message model

    THis provides a user-friendly interface to manage manage messages that is:
    create, view and manage messages.
    
    """

    # Fields to display in the list view
    list_display = ['senderr', 'receiver', 'content_preview', 'timestamp']

    # Fields to filter by in the sidebar
    list_filter = ['timestamp','sender','receiver']

    # Fields to search by 
    search_field = ['sender_username','receiver_username','content']

    # Fields that are read only 
    readoly_fields = ['timestamp']


    # Ad date hierarchy for easy navigation
    date_hierarchy = 'timestamp'

    # Optimize the database queries by selecting related objects
    list_select_related = ['sender', 'receiver']

    def content_preview(self, obj):
        """
        custom methodd to show a preview of the message content
        """
        return obj.content[:50] + "..." if len(obj).content > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for the notification model

    This will show all the newly created notifications in the admin interface
    """
    # Fields to display in the list view
    list_display = ['user', 'content_preview', 'timestamp', 'is_read','related_message']

    # Fields to filter by in the sidebar
    list_filter = ['timestamp', 'is_read', 'user']

    # Fields to search by
    search_fields = ['user_username', 'content']

    # Fields that are read only
    readonly_fields = ['timestamp']

    # Add date to hierarchy for easy navigation
    date_hierarchy = 'timestamp'

    def content_preview(self, obj):

        return obj.content[:50] + "...." if len(obj.content) > 50 else obj.content
    
    content_preview.short_description = 'Content Preview'

    def related_message(self, obj):
        if obj.message:
            return f"Message from {obj.message.sender.username}"
        return "No related message"
    related_message.short_description = 'Related Message'

    def mark_as_read(self, request, queryset):
        # Admin action to mark selected notification as read
        updated = queryset.update(is_read= True)
        self.message_user(request, f'{updated} notifications were marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"


    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read = False)
        self.message_user(request, f"{updated} notifications were marked as unread")
    mark_as_unread.short_description = "Mark selected notifications as unread"