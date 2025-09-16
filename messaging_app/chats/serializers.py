from rest_framework import serializers
from .models import CustomUser, Conversation, Message


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ["id", "username", "first_name", 
                  "last_name", "email", "password", "password_hash",
                  "phone_number", "role", "created_at"]
        
    def create(self, validated_data):
        password = validated_data.pop("password")
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user
        
class ConversationSerializer(serializers.ModelSerializer):
    participants_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    class Meta:
        model = Conversation
        fields = ["id", "participants", "created_at"]
        query_set = CustomUser.objects.all()

class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    class Meta:
        model = Message
        fields = ("id", "sender_id", "message_body", "sent_at")
