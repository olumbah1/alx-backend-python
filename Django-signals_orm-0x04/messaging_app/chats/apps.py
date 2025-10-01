from django.apps import AppConfig


class MessagingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chats'
    verbose_name = 'Messaging System'

    def ready(self):
        """
        Import signal handlers when the app is ready.
        This ensures signals are registered and active.
        """
        # Import signals to register them
        import messaging.signals
        
        print("✅ Messaging app signals registered")