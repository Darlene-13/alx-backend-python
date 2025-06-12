from django.contrib import admin
from .models import Message, Notification, MessageHistory
from django.utils.html import format_html
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.urls import reverse

class MessageHistoryInline(admin.TabularInline):
    """
    Inline admin interface for messageHhistory model
    This allows us to see the message edit history within the message admin
    
    """
    model = MessageHistory
    extra = 0
    readonly_fields = ['old_content', 'edited_at', 'edited_by', 'content_preview']
    fields = ['comtent_preview', 'edited_at', 'edited_by', 'edit_reason']

    def content_preview(self, obj):
        """
        Show a previews of the old content"""

        if obj.old_content:
            return obj.old_content[:100] + "....." if len(obj).old_content > 100 else obj.old_content
        return "No content"
    content_preview.short_description = "Old Content Preview"

    def has_add_permission(self, request, obj=None):
        """ Disable adding history manually, as it should be automatic """
        return False

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interfacee for the message model

    THis provides a user-friendly interface to manage manage messages that is:
    create, view and manage messages.
    
    """

    # Fields to display in the list view
    list_display = ['sender', 'receiver', 'content_preview', 'timestamp', 'edied_status', 'edit_count_display']

    # Fields to filter by in the sidebar
    list_filter = ['timestamp''edited','last_edited', 'sender','receiver']

    # Fields to search by 
    search_field = ['sender_username','receiver_username','content']

    # Fields that are read only 
    readoly_fields = ['timestamp', 'last_edited', 'edit_count_display']


    # Ad date hierarchy for easy navigation
    date_hierarchy = 'timestamp'

    # Optimize the database queries by selecting related objects
    list_select_related = ['sender', 'receiver']

    # Add history inline
    inlines = [MessageHistoryInline]

    fieldsets = (
        ('Message Details', {
            'fields': ('sender', 'receiver','content')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'last_edited', 'edited'),
            'classes': ('collapse',), # collapsible section
        }),
        ('statistics'), {

            'fields': ('edite_count_display',),
            'classes': ('collapse',), # collapsible section
        }
    )

    def content_preview(self, obj):
        """
        custom methodd to show a preview of the message content
        """
        return obj.content[:50] + "..." if len(obj).content > 50 else obj.content
    content_preview.short_description = 'Content Preview'


    def edited_status(self, obj):
        if obj.edited:
            return format_html(
                '<span style="color: orange;">Edited</span>'
            )
        return format_html(
            '<span style="color: green;">Original</span>'
        )
    edited_status.short_description = 'Edit status'

    def edit_count_display(self, obj):
        """
        Display the number of edits for this message"""

        count = obj.edit_count
        if count > 0:
            return format_html(
                '<strong>{}edit{}</strong>', count,'s' if count !=1 else '' 
            )
        return "No edits"
    edit_count_display.short_description = "Edit Count"



    # Custom admin actions
    def mark_as_edited(self, request, queryset):
        """
        Admin action to manually mark the messages as edited (for testing)"""

        updated = queryset.update(edited = True, last_edited = timezone.now())
        self.message_user(request , f'{updated} messages were marked as edited.')
    mark_as_edited.short_description = "Mark selected messages as edited"

@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for the notification model

    This will show all the newly created notifications in the admin interface
    """
    # Fields to display in the list view
    list_display = ['user', 'content_preview', 'timestamp', 'is_read','related_message', 'edited_at', 'edited_by']

    # Fields to filter by in the sidebar
    list_filter = ['timestamp', 'is_read', 'user', 'edited_at', 'edited_by', 'message__sender']

    # Fields to search by
    search_fields = ['user_username', 'content', 'edited_by__username']

    # Fields that are read only
    readonly_fields = ['timestamp', 'message', 'edited_by', 'edited_at', 'old_content', 'content_preview']

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