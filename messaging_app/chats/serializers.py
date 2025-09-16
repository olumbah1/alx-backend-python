from rest_framework import serializers
from .models import CustomUser, Conversation, Message


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ["user_id", "username", "first_name", 
                  "last_name", "email", "password",
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
        fields = ["conversation_id", "participants", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField() 
    
    class Meta:
        model = Message
        fields = ['message_id', 'sender', 'message_body', 'sent_at', 'full_name']
    
    def validate_message_body(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        if len(value) > 250:
            raise serializers.ValidationError("Message too long. Max 250 characters.")
        return value
    
    def get_full_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender_id.last_name}"