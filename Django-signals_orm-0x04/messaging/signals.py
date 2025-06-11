from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, Notification

@receiver(post_save, sender= Message)
def create_notification(sender, instance, created, **kwargs):
    """
    Signal handler that automatically create a notification when a new message is created
    
    This function is triggered after a new Message instance is saved
    Since we are creating notifications for new_messages only (created=True)
    """
    if created:
        # Create a notification for the message receiver
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            content = f"You have a new message from {instance.sender.username}: '{instance.content[:50]}....."  
        )

@receiver(post_save, sender=Notification)
def message_saved(sender, instance, created, **kwargs):
    """
    Signal handler for message events
    This demonstrates how multiple signals can be used to handle multiple events
    """
    if created:
        print(f"New message created: {instance.sender.username} -> {instance.receiver.username}")
    else:
        print(f" Message updated: {instance.id}")