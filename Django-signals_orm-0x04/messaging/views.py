from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import Message, Notification, MessageHistory
from django.contrib import messages as django_messages
from django.db.models import Q, Prefetch, Count


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


@login_required
def conversation_list(request):
    """
    View to display all conversation threads for the current user.
    Uses optimized queries with select_related and prefetch_related.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template with conversation threads
    """
    # Get all threads involving the user with optimized queries
    threads = Message.get_user_threads(request.user)
    
    # Add reply count annotation for each thread
    threads_with_counts = []
    for thread in threads:
        thread_data = {
            'message': thread,
            'reply_count': thread.get_reply_count(),
            'total_reply_count': thread.get_total_reply_count(),
            'other_user': thread.receiver if thread.sender == request.user else thread.sender,
            'last_activity': thread.timestamp,
        }
        threads_with_counts.append(thread_data)
    
    context = {
        'threads': threads_with_counts,
    }
    
    return render(request, 'messaging/conversation_list.html', context)


@login_required
def thread_detail(request, message_id):
    """
    View to display a single threaded conversation.
    Shows the root message and all nested replies in a threaded format.
    Uses optimized recursive querying.
    
    Args:
        request: HTTP request object
        message_id: ID of the root message
        
    Returns:
        Rendered template with threaded conversation
    """
    # Get the message with optimized query
    message = get_object_or_404(
        Message.objects.select_related('sender', 'receiver', 'parent_message'),
        id=message_id
    )
    
    # Check if user is part of this conversation
    root_message = message.get_thread_root()
    participants = root_message.get_thread_participants()
    
    if request.user not in participants:
        django_messages.error(request, 'You do not have permission to view this conversation.')
        return redirect('conversation_list')
    
    # Get all messages in thread with optimized query
    thread_messages = root_message.get_thread_messages()
    
    # Build threaded structure
    def build_thread_tree(parent_msg, all_messages):
        """
        Recursively build a nested structure for template rendering.
        """
        thread_tree = {
            'message': parent_msg,
            'replies': []
        }
        
        # Find direct replies
        for msg in all_messages:
            if msg.parent_message and msg.parent_message.id == parent_msg.id:
                thread_tree['replies'].append(build_thread_tree(msg, all_messages))
        
        return thread_tree
    
    # Build the threaded structure
    thread_tree = build_thread_tree(root_message, thread_messages)
    
    # Mark messages as read if user is receiver
    for msg in thread_messages:
        if msg.receiver == request.user and not msg.is_read:
            msg.mark_as_read()
    
    context = {
        'root_message': root_message,
        'thread_tree': thread_tree,
        'participants': participants,
        'total_messages': len(thread_messages),
    }
    
    return render(request, 'messaging/thread_detail.html', context)


@login_required
def send_reply(request, parent_message_id):
    """
    View to send a reply to a specific message.
    
    Args:
        request: HTTP request object
        parent_message_id: ID of the parent message
        
    Returns:
        Redirect to thread detail or JSON response
    """
    if request.method != 'POST':
        django_messages.error(request, 'Invalid request method.')
        return redirect('conversation_list')
    
    # Get the parent message
    parent_message = get_object_or_404(
        Message.objects.select_related('sender', 'receiver'),
        id=parent_message_id
    )
    
    # Check if user is part of the conversation
    if request.user not in [parent_message.sender, parent_message.receiver]:
        django_messages.error(request, 'You cannot reply to this message.')
        return redirect('conversation_list')
    
    content = request.POST.get('content', '').strip()
    
    if not content:
        django_messages.error(request, 'Reply content cannot be empty.')
        return redirect('thread_detail', message_id=parent_message.get_thread_root().id)
    
    # Determine receiver (the other person in the conversation)
    receiver = parent_message.sender if request.user == parent_message.receiver else parent_message.receiver
    
    # Create the reply message
    reply = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content,
        parent_message=parent_message
    )
    
    django_messages.success(request, 'Reply sent successfully!')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message_id': reply.id,
            'parent_message_id': parent_message_id
        })
    
    # Redirect to the thread root
    return redirect('thread_detail', message_id=parent_message.get_thread_root().id)


@login_required
def start_conversation(request):
    """
    View to start a new conversation thread.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered template or redirect
    """
    if request.method == 'POST':
        receiver_username = request.POST.get('receiver', '').strip()
        content = request.POST.get('content', '').strip()
        
        if not receiver_username or not content:
            django_messages.error(request, 'Please provide both receiver and message content.')
            return render(request, 'messaging/start_conversation.html')
        
        try:
            receiver = User.objects.get(username=receiver_username)
            
            if receiver == request.user:
                django_messages.error(request, 'You cannot send a message to yourself.')
                return render(request, 'messaging/start_conversation.html')
            
            # Create the root message (no parent)
            message = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                content=content,
                parent_message=None  # Root message
            )
            
            django_messages.success(request, f'Message sent to {receiver_username}!')
            return redirect('thread_detail', message_id=message.id)
            
        except User.DoesNotExist:
            django_messages.error(request, f'User "{receiver_username}" does not exist.')
            return render(request, 'messaging/start_conversation.html')
    
    # GET request - show form
    # Get all users except current user
    users = User.objects.exclude(id=request.user.id).order_by('username')
    
    context = {
        'users': users,
    }
    
    return render(request, 'messaging/start_conversation.html', context)


@login_required
def conversation_with_user(request, username):
    """
    View to display all conversation threads with a specific user.
    
    Args:
        request: HTTP request object
        username: Username of the other user
        
    Returns:
        Rendered template with conversations
    """
    other_user = get_object_or_404(User, username=username)
    
    if other_user == request.user:
        django_messages.error(request, 'You cannot view conversations with yourself.')
        return redirect('conversation_list')
    
    # Get all threads between these two users
    threads = Message.get_conversation_threads(request.user, other_user)
    
    # Add statistics
    threads_with_stats = []
    for thread in threads:
        thread_data = {
            'message': thread,
            'reply_count': thread.get_reply_count(),
            'total_reply_count': thread.get_total_reply_count(),
        }
        threads_with_stats.append(thread_data)
    
    context = {
        'other_user': other_user,
        'threads': threads_with_stats,
    }
    
    return render(request, 'messaging/conversation_with_user.html', context)


@login_required
def get_message_replies_json(request, message_id):
    """
    API endpoint to get all replies for a message in JSON format.
    Useful for dynamic loading or AJAX requests.
    
    Args:
        request: HTTP request object
        message_id: ID of the message
        
    Returns:
        JSON response with replies
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Check permission
    if request.user not in [message.sender, message.receiver]:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get all replies recursively
    replies = message.get_all_replies_recursive()
    
    # Format for JSON
    replies_data = []
    for reply in replies:
        replies_data.append({
            'id': reply.id,
            'sender': reply.sender.username,
            'receiver': reply.receiver.username,
            'content': reply.content,
            'timestamp': reply.timestamp.isoformat(),
            'is_read': reply.is_read,
            'edited': reply.edited,
            'parent_id': reply.parent_message.id if reply.parent_message else None,
        })
    
    return JsonResponse({
        'message_id': message.id,
        'reply_count': len(replies),
        'replies': replies_data
    })


@login_required
def thread_statistics(request, message_id):
    """
    View to display statistics for a conversation thread.
    
    Args:
        request: HTTP request object
        message_id: ID of the root message
        
    Returns:
        JSON response with statistics
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Get thread root
    root = message.get_thread_root()
    
    # Check permission
    participants = root.get_thread_participants()
    if request.user not in participants:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get all thread messages
    thread_messages = root.get_thread_messages()
    
    # Calculate statistics
    total_messages = len(thread_messages)
    messages_by_user = {}
    
    for msg in thread_messages:
        username = msg.sender.username
        messages_by_user[username] = messages_by_user.get(username, 0) + 1
    
    stats = {
        'thread_id': root.id,
        'total_messages': total_messages,
        'participants': [u.username for u in participants],
        'messages_by_user': messages_by_user,
        'created_at': root.timestamp.isoformat(),
        'max_depth': calculate_thread_depth(root),
    }
    
    return JsonResponse(stats)


def calculate_thread_depth(message, current_depth=1):
    """
    Calculate the maximum depth of a thread.
    
    Args:
        message: The root message
        current_depth: Current depth level
        
    Returns:
        Maximum depth as integer
    """
    replies = message.get_replies()
    
    if not replies:
        return current_depth
    
    max_depth = current_depth
    for reply in replies:
        depth = calculate_thread_depth(reply, current_depth + 1)
        max_depth = max(max_depth, depth)
    
    return max_depth