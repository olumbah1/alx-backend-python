from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, ConversationViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'customuser', CustomUserViewSet, basename='customuser')
router.register(r'conversation', ConversationViewSet, basename='conversation')
router.register(r'message', MessageViewSet, basename='message')

urlpatterns = router.urls