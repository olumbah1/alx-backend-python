import logging
from datetime import datetime, timedelta
import os
from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from collections import defaultdict
import threading

def setup_request_logger():
    """Setup the request logger with file handler."""
    # Get the base directory (where manage.py is located)
    base_dir = getattr(settings, 'BASE_DIR', os.getcwd())
    log_directory = os.path.join(base_dir, 'logs')
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    
    # Create a logger specifically for request logging
    request_logger = logging.getLogger('request_logger')
    
    # Only set up if not already configured
    if not request_logger.handlers:
        request_logger.setLevel(logging.INFO)
        
        # Create file handler
        log_file_path = os.path.join(log_directory, 'user_requests.log')
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        request_logger.addHandler(file_handler)
    
    return request_logger


class RequestLoggingMiddleware:
    """
    Middleware to log user requests with timestamp, user, and request path.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response
        # Set up the logger when middleware is initialized
        self.request_logger = setup_request_logger()

    def __call__(self, request):
        """
        Process the request and log the information.
        
        Args:
            request: The HTTP request object
            
        Returns:
            The HTTP response from the next middleware/view
        """
        # Get user information
        if hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user.username
        else:
            user = 'Anonymous'
        
        # Log the request information
        log_message = f"{datetime.now()} - User: {user} - Path: {request.path}"
        self.request_logger.info(log_message)
        
        # Continue processing the request
        response = self.get_response(request)
        
        return response


class RestrictAccessByTimeMiddleware:
    """
    Middleware to restrict access to the messaging app during certain hours.
    Access is allowed only between 6 AM (06:00) and 9 PM (21:00).
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response
        self.allowed_start_hour = 6   # 6 AM
        self.allowed_end_hour = 21    # 9 PM

    def __call__(self, request):
        """
        Process the request and check if access is allowed based on current time.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponseForbidden if access is denied, otherwise the normal response
        """
        # Get current server time
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Check if current time is outside allowed hours
        if current_hour < self.allowed_start_hour or current_hour >= self.allowed_end_hour:
            # Create forbidden response with custom message
            forbidden_message = f"""
            <html>
                <head><title>Access Denied</title></head>
                <body>
                    <h1>403 - Access Forbidden</h1>
                    <p>The messaging application is only available between 6:00 AM and 9:00 PM.</p>
                    <p>Current server time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Please try again during allowed hours (6:00 AM - 9:00 PM).</p>
                </body>
            </html>
            """
            return HttpResponseForbidden(forbidden_message)
        
        # If within allowed hours, continue processing the request
        response = self.get_response(request)
        return response


class OffensiveLanguageMiddleware:
    """
    Middleware that limits the number of chat messages a user can send within 
    a certain time window, based on their IP address.
    
    Rate limit: 5 messages per minute per IP address
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response
        # Dictionary to store message timestamps for each IP address
        # Format: {ip_address: [timestamp1, timestamp2, ...]}
        self.ip_message_history = defaultdict(list)
        # Thread lock for thread-safe access to the message history
        self.lock = threading.Lock()
        # Rate limiting configuration
        self.max_messages = 5  # Maximum messages allowed
        self.time_window = 60  # Time window in seconds (1 minute)

    def get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        
        Args:
            request: The HTTP request object
            
        Returns:
            str: The client's IP address
        """
        # Check for IP in forwarded headers (for reverse proxies/load balancers)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, get the first one
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Get IP from REMOTE_ADDR
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def clean_old_messages(self, ip_address, current_time):
        """
        Remove message timestamps that are outside the time window.
        
        Args:
            ip_address: The IP address to clean
            current_time: Current timestamp
        """
        cutoff_time = current_time - timedelta(seconds=self.time_window)
        # Keep only messages within the time window
        self.ip_message_history[ip_address] = [
            timestamp for timestamp in self.ip_message_history[ip_address]
            if timestamp > cutoff_time
        ]

    def is_rate_limited(self, ip_address):
        """
        Check if the IP address has exceeded the rate limit.
        
        Args:
            ip_address: The IP address to check
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        current_time = datetime.now()
        
        with self.lock:
            # Clean old message timestamps
            self.clean_old_messages(ip_address, current_time)
            
            # Check if the IP has exceeded the limit
            message_count = len(self.ip_message_history[ip_address])
            
            if message_count >= self.max_messages:
                return True
            
            # Add current timestamp to the history
            self.ip_message_history[ip_address].append(current_time)
            return False

    def __call__(self, request):
        """
        Process the request and apply rate limiting for POST requests (messages).
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: Either the blocked response or the normal response
        """
        # Only apply rate limiting to POST requests (chat messages)
        if request.method == 'POST':
            # Get the client's IP address
            client_ip = self.get_client_ip(request)
            
            # Check if this IP is rate limited
            if self.is_rate_limited(client_ip):
                # Create rate limit response
                error_message = {
                    'error': 'Rate limit exceeded',
                    'message': f'You can only send {self.max_messages} messages per minute. Please wait before sending another message.',
                    'retry_after': self.time_window
                }
                
                # Return JSON response for API calls or HTML for regular requests
                if request.content_type == 'application/json' or 'api' in request.path:
                    response = JsonResponse(error_message, status=429)
                    response['Retry-After'] = str(self.time_window)
                    return response
                else:
                    # HTML response for regular form submissions
                    html_message = f"""
                    <html>
                        <head><title>Rate Limit Exceeded</title></head>
                        <body>
                            <h1>429 - Rate Limit Exceeded</h1>
                            <p><strong>You are sending messages too quickly!</strong></p>
                            <p>You can only send {self.max_messages} messages per minute.</p>
                            <p>Please wait before sending another message.</p>
                            <p>Your IP: {client_ip}</p>
                            <p><a href="javascript:history.back()">Go Back</a></p>
                        </body>
                    </html>
                    """
                    response = HttpResponseForbidden(html_message)
                    response.status_code = 429  # Too Many Requests
                    response['Retry-After'] = str(self.time_window)
                    return response
        
        # Continue processing the request if not rate limited
        response = self.get_response(request)
        return response

class RolepermissionMiddleware:
    """
    Middleware that checks the user's role before allowing access to specific actions.
    Only allows admin and moderator users to access certain protected paths.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response: The next middleware or view in the chain
        """
        self.get_response = get_response
        
        # Define protected paths that require admin/moderator access
        self.protected_paths = [
            '/admin/',
            '/manage/',
            '/moderate/',
            '/delete/',
            '/ban/',
            '/settings/',
            '/users/',
            '/reports/',
            '/dashboard/',
        ]
        
        # Define allowed roles
        self.allowed_roles = ['admin', 'moderator']

    def get_user_role(self, user):
        """
        Get the user's role from various possible sources.
        
        Args:
            user: Django User object
            
        Returns:
            str: The user's role or None if no role found
        """
        if not user.is_authenticated:
            return None
            
        # Method 1: Check if user is superuser (Django built-in admin)
        if user.is_superuser:
            return 'admin'
            
        # Method 2: Check if user is staff (Django built-in staff)
        if user.is_staff:
            return 'moderator'
            
        # Method 3: Check for custom role field on User model
        if hasattr(user, 'role'):
            return getattr(user, 'role', None)
            
        # Method 4: Check for role in user profile
        if hasattr(user, 'profile') and hasattr(user.profile, 'role'):
            return getattr(user.profile, 'role', None)
            
        # Method 5: Check for role through groups
        user_groups = user.groups.values_list('name', flat=True)
        for group_name in user_groups:
            group_lower = group_name.lower()
            if group_lower in ['admin', 'administrator']:
                return 'admin'
            elif group_lower in ['moderator', 'mod']:
                return 'moderator'
                
        # Method 6: Check for custom role through related model
        if hasattr(user, 'userrole'):
            return getattr(user.userrole, 'role', None)
            
        return None

    def requires_role_check(self, path):
        """
        Check if the requested path requires role verification.
        
        Args:
            path: The request path
            
        Returns:
            bool: True if path requires role check, False otherwise
        """
        # Check if the path starts with any of the protected paths
        return any(path.startswith(protected_path) for protected_path in self.protected_paths)

    def __call__(self, request):
        """
        Process the request and check user role for protected paths.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HttpResponse: Either access denied response or the normal response
        """
        # Check if this path requires role verification
        if self.requires_role_check(request.path):
            
            # Check if user is authenticated
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                # User not authenticated - redirect to login or return 401
                forbidden_message = """
                <html>
                    <head><title>Authentication Required</title></head>
                    <body>
                        <h1>401 - Authentication Required</h1>
                        <p>You must be logged in to access this resource.</p>
                        <p>Please <a href="/login/">log in</a> to continue.</p>
                    </body>
                </html>
                """
                response = HttpResponseForbidden(forbidden_message)
                response.status_code = 401  # Unauthorized
                return response
            
            # Get user's role
            user_role = self.get_user_role(request.user)
            
            # Check if user has required role
            if user_role not in self.allowed_roles:
                # User doesn't have required role - return 403
                user_info = f"User: {request.user.username}" if request.user.is_authenticated else "Anonymous User"
                role_info = f"Role: {user_role}" if user_role else "Role: None"
                
                forbidden_message = f"""
                <html>
                    <head><title>Access Denied - Insufficient Permissions</title></head>
                    <body>
                        <h1>403 - Access Forbidden</h1>
                        <p><strong>You do not have permission to access this resource.</strong></p>
                        <p>This action requires admin or moderator privileges.</p>
                        <hr>
                        <p><strong>Your Information:</strong></p>
                        <p>{user_info}</p>
                        <p>{role_info}</p>
                        <p>Required roles: Admin or Moderator</p>
                        <hr>
                        <p>If you believe this is an error, please contact your system administrator.</p>
                        <p><a href="javascript:history.back()">Go Back</a> | <a href="/">Home</a></p>
                    </body>
                </html>
                """
                
                # For API requests, return JSON response
                if request.content_type == 'application/json' or 'api' in request.path:
                    error_response = {
                        'error': 'Access Denied',
                        'message': 'You do not have permission to access this resource.',
                        'required_roles': self.allowed_roles,
                        'your_role': user_role,
                        'user': request.user.username if request.user.is_authenticated else None
                    }
                    return JsonResponse(error_response, status=403)
                
                return HttpResponseForbidden(forbidden_message)
        
        # Continue processing the request if role check passed or not required
        response = self.get_response(request)
        return response