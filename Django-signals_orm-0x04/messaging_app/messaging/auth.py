# # authentication.py
# from rest_framework.authentication import BaseAuthentication
# from rest_framework.exceptions import AuthenticationFailed
# from .models import CustomJWT

# class CustomJWTAuthentication(BaseAuthentication):
#     """
#     Custom JWT Token authentication.
#     Clients should authenticate by passing the token key in the "Authorization"
#     HTTP header, prepended with the string "Bearer ".  For example:
#         Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a
#     """
    
#     keyword = 'Bearer'
#     model = CustomJWT

#     def authenticate(self, request):
#         auth = self.get_authorization_header(request).split()

#         if not auth or auth[0].lower() != self.keyword.lower().encode():
#             return None

#         if len(auth) == 1:
#             raise AuthenticationFailed('Invalid token header. No credentials provided.')
#         elif len(auth) > 2:
#             raise AuthenticationFailed('Invalid token header. Token string should not contain spaces.')

#         try:
#             token = auth[1].decode()
#         except UnicodeError:
#             raise AuthenticationFailed('Invalid token header. Token string should not contain invalid characters.')

#         return self.authenticate_credentials(token)

#     def authenticate_credentials(self, key):
#         try:
#             token = self.model.objects.get(key=key)
#         except self.model.DoesNotExist:
#             raise AuthenticationFailed('Invalid token.')

#         if not token.user.is_active:
#             raise AuthenticationFailed('User inactive or deleted.')

#         return (token.user, token)

#     def get_authorization_header(self, request):
#         """
#         Return request's 'Authorization:' header, as a bytestring.
#         """
#         auth = request.META.get('HTTP_AUTHORIZATION', b'')
#         if isinstance(auth, str):
#             auth = auth.encode('iso-8859-1')
#         return auth
