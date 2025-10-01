from django.urls import path
from . import views

urlpatterns = [
    # User dashboard
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    
    # User deletion
    path('delete-account/', views.delete_user, name='delete_user'),
    path('delete-account/success/', views.delete_user_success, name='delete_user_success'),
    
    # Messaging
    path('send/', views.send_message, name='send_message'),
    path('message/<int:message_id>/', views.message_detail, name='message_detail'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    
    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]