from rest_framework import serializers
from .models import CustomUser, Conversation, Message
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.contrib.auth import authenticate

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ["user_id", "username", "first_name", 
                  "last_name", "email", "password",
                  "phone_number", "role", "created_at"]
        extra_kwargs = {
            'password': {'write_only': True},
            'created_at': {'read_only': True},
            'user_id': {'read_only': True}
        }
        
    def create(self, validated_data):
        password = validated_data.pop("password")
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise DRFValidationError({"password": list(e.messages)})
        
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        # Handle password update separately
        password = validated_data.pop('password', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            try:
                validate_password(password)
            except DjangoValidationError as e:
                raise DRFValidationError({"password": list(e.messages)})
            instance.set_password(password)
        
        instance.save()
        return instance


class CustomUserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", 
                  "password", "confirm_password", "phone_number", "role"]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.pop('confirm_password', None)
        
        if password != confirm_password:
            raise DRFValidationError({"confirm_password": "Passwords don't match"})
        
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop("password")
        
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise DRFValidationError({"password": list(e.messages)})
        
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomUserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if not username or not password:
            raise DRFValidationError('Must include username and password')
        
        user = authenticate(username=username, password=password)
        if not user:
            raise DRFValidationError('Invalid username or password')
        
        if not user.is_active:
            raise DRFValidationError('User account is disabled')
        
        attrs['user'] = user
        return attrs


class ConversationSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(), 
        many=True
    )
    participant_details = CustomUserSerializer(
        source='participants', 
        many=True, 
        read_only=True
    )
    
    class Meta:
        model = Conversation
        fields = ["conversation_id", "participants", "participant_details", "created_at"]
        extra_kwargs = {
            'conversation_id': {'read_only': True},
            'created_at': {'read_only': True}
        }


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_details = CustomUserSerializer(source='sender', read_only=True)
    
    class Meta:
        model = Message
        fields = ['message_id', 'sender', 'conversation', 'message_body', 
                  'sent_at', 'sender_name', 'sender_details']
        extra_kwargs = {
            'message_id': {'read_only': True},
            'sent_at': {'read_only': True}
        }
    
    def validate_message_body(self, value):
        if not value or not value.strip():
            raise DRFValidationError("Message cannot be empty.")
        
        if len(value.strip()) > 250:
            raise DRFValidationError("Message too long. Maximum 250 characters allowed.")
        
        return value.strip()
    
    def get_sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip()


