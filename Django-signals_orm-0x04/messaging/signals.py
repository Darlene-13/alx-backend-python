from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Message, Notification, MessageHistory
from django.utils import timezone

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

@receiver(pre_save, sender=Message)
def log_message_edit_history(sender, instance, **kwargs):
    """ 
    Signal handler that logs the old content of a message before it's edited

    This functions is triggered before a Message is saved
    It captures the old content and stores it in MessageHistory if the message is being edited
    
    """

    if kwargs.get('raw', False):
        return 
    
    if instance.pk:
        try:

            old_message = Message.objects.get(pk=instance.pk)

            if old_message.content !=instance.content:

                MessageHistory.objects.create(
                    message= old_message,
                    old_content = old_message.content,
                    edited_at = timezone.now(),
                    edited_by = instance.sender
                )
                if not instance.edited:
                    instance.edited = True
                    instance.last_edited = timezone.now()
                
                print (f"Message edit logged: {old_message.id} - Content changed")
        except Message.DoesNotExist:
            # THis should not happen in normal operation
            print(f"Warning: Could not find original message with ID {instance.pk} for history logging.")


@receiver(post_save, sender=Message)
def create_edit_notification(sender, instance, created, **kwargs):
    """
    Signal handler that creates a notification when a message is edited
    THis runs after the message is saved and creates a notification for the 
    receiver if the message was edited(not newly created)
    """
    if created:
        return
    
    # SKip for raw saves
    if kwargs.get('raw', False):
        return
    
    # Check if this message was an edit
    if instance.edited and instance.notfication.exists():
        Notification.objects.create(
            user = instance.receiver,
            message= instance, 
            content = f"{instance.sender.username} edited their message: '{instance.content[:50]}........"
        )

    print (f"Edit notification created for {instance.receiver.username}")






@receiver(post_save, sender=Notification)
def message_saved(sender, instance, created, **kwargs):
    """
    Signal handler for message events
    This demonstrates how multiple signals can be used to handle multiple events
    """
    if created: # Only create notification for new messages not updates
        print(f"New message created: {instance.sender.username} -> {instance.receiver.username}")
    else:
        print(f" Message updated: {instance.id}")