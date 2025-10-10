from rest_framework import permissions
from .models import Conversation

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

class IsParticipantOfConversation(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        conversation = obj.conversation if hasattr(obj, 'conversation') else obj
        if request.method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            return request.user in conversation.participants.all()
        return False


