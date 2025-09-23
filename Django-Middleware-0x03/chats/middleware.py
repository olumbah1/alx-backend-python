import logging
from datetime import datetime
import os
from django.conf import settings
from django.http import HttpResponseForbidden

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