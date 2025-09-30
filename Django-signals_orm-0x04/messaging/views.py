from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import Message, Notification, MessageHistory


@login_required
@require_http_methods(["GET", "POST"])
def delete_user(request):
    """
    View to handle user account deletion.
    
    GET: Display confirmation page
    POST: Delete the user account
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or redirect
    """
    if request.method == 'POST':
        # Get the password confirmation
        password = request.POST.get('password', '')
        confirm_text = request.POST.get('confirm_text', '')
        
        # Verify password
        if not request.user.check_password(password):
            messages.error(request, 'Incorrect password. Account deletion cancelled.')
            return render(request, 'messaging/delete_user.html')
        
        # Verify confirmation text
        if confirm_text != 'DELETE':
            messages.error(request, 'Please type "DELETE" to confirm account deletion.')
            return render(request, 'messaging/delete_user.html')
        
        # Get user statistics before deletion
        user = request.user
        username = user.username
        
        # Count related data (for logging/display purposes)
        sent_messages_count = Message.objects.filter(sender=user).count()
        received_messages_count = Message.objects.filter(receiver=user).count()
        notifications_count = Notification.objects.filter(user=user).count()
        
        # Log the deletion (optional)
        print(f"🗑️  Deleting user: {username}")
        print(f"   - Sent messages: {sent_messages_count}")
        print(f"   - Received messages: {received_messages_count}")
        print(f"   - Notifications: {notifications_count}")
        
        # Logout the user before deletion
        logout(request)
        
        # Delete the user (signals will handle related data cleanup)
        user.delete()
        
        # Add success message
        messages.success(
            request, 
            f'Account "{username}" has been successfully deleted along with all associated data.'
        )
        
        # Redirect to homepage or registration page
        return redirect('delete_user_success')
    
    # GET request - show confirmation page
    # Get user statistics to show what will be deleted
    context = {
        'sent_messages_count': Message.objects.filter(sender=request.user).count(),
        'received_messages_count': Message.objects.filter(receiver=request.user).count(),
        'notifications_count': Notification.objects.filter(user=request.user).count(),
    }
    
    return render(request, 'messaging/delete_user.html', context)


def delete_user_success(request):
    """
    View to display after successful user deletion.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template
    """
    return render(request, 'messaging/delete_user_success.html')


@login_required
def user_dashboard(request):
    """
    User dashboard showing messages and notifications.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template with user data
    """
    # Get user's messages
    sent_messages = Message.objects.filter(sender=request.user).order_by('-timestamp')[:10]
    received_messages = Message.objects.filter(receiver=request.user).order_by('-timestamp')[:10]
    
    # Get user's notifications
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')[:10]
    unread_notifications = Notification.get_unread_count(request.user)
    
    context = {
        'sent_messages': sent_messages,
        'received_messages': received_messages,
        'notifications': notifications,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'messaging/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def send_message(request):
    """
    View to send a message to another user.
    
    Args:
        request: HTTP request object
        
    Returns:
        JSON response or redirect
    """
    receiver_username = request.POST.get('receiver')
    content = request.POST.get('content')
    
    # Validate input
    if not receiver_username or not content:
        messages.error(request, 'Please provide both receiver and message content.')
        return redirect('user_dashboard')
    
    try:
        receiver = User.objects.get(username=receiver_username)
        
        # Don't allow sending messages to self
        if receiver == request.user:
            messages.error(request, 'You cannot send a message to yourself.')
            return redirect('user_dashboard')
        
        # Create the message (signal will create notification automatically)
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content
        )
        
        messages.success(request, f'Message sent to {receiver_username}!')
        
        # Return JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Message sent successfully',
                'message_id': message.id
            })
        
        return redirect('user_dashboard')
        
    except User.DoesNotExist:
        messages.error(request, f'User "{receiver_username}" does not exist.')
        return redirect('user_dashboard')


@login_required
def message_detail(request, message_id):
    """
    View to display a single message with its edit history.
    
    Args:
        request: HTTP request object
        message_id: ID of the message to display
        
    Returns:
        Rendered template with message details
    """
    try:
        # Get the message
        message = Message.objects.get(id=message_id)
        
        # Check if user is sender or receiver
        if request.user not in [message.sender, message.receiver]:
            messages.error(request, 'You do not have permission to view this message.')
            return redirect('user_dashboard')
        
        # Mark as read if user is receiver
        if request.user == message.receiver and not message.is_read:
            message.mark_as_read()
        
        # Get edit history
        edit_history = message.get_edit_history()
        
        context = {
            'message': message,
            'edit_history': edit_history,
            'is_sender': request.user == message.sender,
        }
        
        return render(request, 'messaging/message_detail.html', context)
        
    except Message.DoesNotExist:
        messages.error(request, 'Message not found.')
        return redirect('user_dashboard')


@login_required
@require_http_methods(["POST"])
def edit_message(request, message_id):
    """
    View to edit a message (sender only).
    
    Args:
        request: HTTP request object
        message_id: ID of the message to edit
        
    Returns:
        Redirect to message detail
    """
    try:
        message = Message.objects.get(id=message_id)
        
        # Only sender can edit
        if request.user != message.sender:
            messages.error(request, 'You can only edit your own messages.')
            return redirect('user_dashboard')
        
        new_content = request.POST.get('content')
        
        if not new_content:
            messages.error(request, 'Message content cannot be empty.')
            return redirect('message_detail', message_id=message_id)
        
        # Update message (signal will save history automatically)
        message.content = new_content
        message.save()
        
        messages.success(request, 'Message edited successfully!')
        return redirect('message_detail', message_id=message_id)
        
    except Message.DoesNotExist:
        messages.error(request, 'Message not found.')
        return redirect('user_dashboard')


@login_required
def notifications_list(request):
    """
    View to display all notifications for the user.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template with notifications
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    unread_count = Notification.get_unread_count(request.user)
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'messaging/notifications.html', context)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """
    View to mark a notification as read.
    
    Args:
        request: HTTP request object
        notification_id: ID of the notification
        
    Returns:
        Redirect or JSON response
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        return redirect('notifications_list')
        
    except Notification.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
        
        messages.error(request, 'Notification not found.')
        return redirect('notifications_list')


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """
    View to mark all notifications as read for the current user.
    
    Args:
        request: HTTP request object
        
    Returns:
        Redirect or JSON response
    """
    Notification.mark_all_as_read(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications_list')