from django.db import models


class UnreadMessagesManager(models.Manager):
    """
    Custom manager to filter and retrieve unread messages for a user.
    """
    
    def unread_for_user(self, user):
        """
        Get all unread messages for a specific user.
        Optimized with select_related for foreign keys.
        
        Args:
            user: User object
            
        Returns:
            QuerySet of unread messages
        """
        return self.filter(
            receiver=user,
            is_read=False
        ).select_related('sender', 'receiver').order_by('-timestamp')
    
    def unread_count(self, user):
        """
        Get count of unread messages for a user.
        
        Args:
            user: User object
            
        Returns:
            Integer count
        """
        return self.filter(receiver=user, is_read=False).count()