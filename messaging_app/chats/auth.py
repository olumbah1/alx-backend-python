from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import exceptions

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # You can add custom logic here, for example logging or extra validation
        user_auth_tuple = super().authenticate(request)
        if user_auth_tuple is None:
            return None
        
        user, validated_token = user_auth_tuple

        # Example: reject users with some custom condition
        if not user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')

        return user, validated_token
