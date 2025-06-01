
# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Conversation, Message


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_online', 'created_at']
    list_filter = ['is_online', 'is_staff', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_id', 'phone_number', 'profile_picture', 'is_online', 'last_seen')
        }),
    )
    readonly_fields = ['user_id', 'created_at', 'updated_at']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['conversation_id', 'is_group', 'group_name', 'created_by', 'participant_count', 'created_at']
    list_filter = ['is_group', 'created_at']
    search_fields = ['group_name', 'created_by__username']
    filter_horizontal = ['participants']
    readonly_fields = ['conversation_id', 'created_at', 'updated_at']
    
    def participant_count(self, obj):
        return obj.participants.count()
    participant_count.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'sender', 'conversation', 'content_preview', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['content', 'sender__username']
    readonly_fields = ['message_id', 'timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'