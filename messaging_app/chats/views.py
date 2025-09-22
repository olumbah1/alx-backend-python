from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.status import HTTP_403_FORBIDDEN
from django_filters.rest_framework import DjangoFilterBackend

from .models import CustomUser, Conversation, Message
from .serializers import CustomUserSerializer, ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]
    
class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsParticipantOfConversation]

    def perform_create(self, serializer):
        conversation = serializer.save()
        if self.request.user not in conversation.participants.all():
            conversation.participants.add(self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        conversation_id = conversation.id  

        if request.user not in conversation.participants.all():
            return Response(
                {"detail": "You are not a participant of this conversation."},
                status=HTTP_403_FORBIDDEN
            )

        data = request.data.copy()
        data['sender_id'] = request.user.id
        data['conversation'] = conversation_id

        serializer = MessageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsParticipantOfConversation]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['conversation', 'sender']
    
    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(conversation__participants=user)

