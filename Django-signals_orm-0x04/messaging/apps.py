from django.apps import AppConfig

class MessagingConfig(AppConfig):
    """
    Configuration for the Messaging Application

    THis class ensure that DJango signals are properly registered
    when the application is ready
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'messaging'

    def read(self):
        """
        This method is called when the application is ready

        It ensures that our signals in signals.py are registered and triggers the message when an instance is created
        
        """
        try:
            import messaging.signals
        except ImportError:
            pass