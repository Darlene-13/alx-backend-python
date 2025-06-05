import logging
from datetime import datetime, time, timedelta
import os
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from collections import defaultdict, deque

class RequestLoggingMiddleware:
    """
    Middleware to log each users request to a file
    Logs: timestamp, user, nd request path
    """
    def __init__(self, get_response):
        """
        Initializing the middleware,
        get_response is a callabled that takes a request and returns a response
        """
        self.get_response = get_response

        #Logging configuration
        self.setup_logger()

    def setup_logger(self):
        """
        Configure the logger to write to the requests.log files
        """
        # create logs directory if it does not exist
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Set up the logger
        self.logger = logging.getLogger('request_logger')
        self.logger.setLevel(logging.INFO)

        # Create a file handler
        log_file_path = os.path.join(log_dir, 'request.log')
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)

        # Create a formatter
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)

        #Add handler to logger
        self.logger.addHandler(file_handler)

        # Prevent propagation to avaoid duplicate logs
        self.logger.propage = False

    def __call__(self, request):
        """
        Code to be executed for each request before view and after middleware is called
        This is where we log the request information
        """
        # Get user information
        if request.user.is_authenticated:
            user = request.user.username or request.user.email
        else:
            user = 'Anonymous'

        # Create a log message with the specified format
        log_message = f"{datetime.now()} - User: {user} - Path: {request.path}"

        # Log the request information
        self.logger.info(log_message)

        # Call the next middleware or view
        response = self.get_response(request)
        return response
    

class RestrictAccessByTimeMiddleware:
    """
    Middleware that denies access to the messaging app outside certain hours
    """
    def __init__(self, get_response):
        """
        One time configuration
        """
        self.get_response = get_response

        #Define the allowed time range 
        self.start_time = time(9, 0)   # From 9 AM     
        self.end_time = time(18,0) #6PM

    def __init__(self, request):
        """
        Check current server time and deny access outside the required time hours
        Returns 403 Forbidden
        """
        current_time = timezone.now().time()

        if not self.is_access_allowed(current_time):
            return JsonResponse({
                'error': 'Access Denied',
                'message': 'Chat access is only allowed between 9AM and 6PM',
                'Current_time': current_time.strftime('%H:%M:%S'),
            }, status = 403)
        
        response = self.get_response(request)

        return response
    
    def is_access_allowed(self, current_time):
        # Check if the current time falls between the required timeset
        """
        Args: Current_time(datetime.time): Current server time
        Returns: bool: True is access is allowed and false is access is denied
        
        """
        return self.start_time <= current_time <=self.end_time
class OffensiveLanguageMiddleware:
    """
    Mesages that limit the number of chat messaes a user can have with a required window, based on their IP address
    """
    def __init__ (self, get_response):
        self.get_response = get_response

        # Rate limiting configuration
        self.max_message = 5
        self.time_window = 60

        # Dictionary to store IP addressess message timestamp
        # Format: { ip_address: deque(timestamp1, timestamp2)}
        self.ip_message_times = defaultdict(deque) # deque is a double ended queue and part of python collections module, behaves like a list but it's optimised for fast appends and pops from both ends making with a time comolexity of 0(1)

        #set up logging for rate limiting events
        self.setup_rate_limit_logger()

    def setup_rate_limit_logger(self):
        """
        Set up logging for rate limiting events
        """
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.rate_limit_logger = logging.getlogger('rate_limit_logger')
        self.rate_limit_logger.setLevel(logging.INFO)

        # Remove existing handlers to handle duplicates
        if self.rate_limit_logger.handlers:
            self.rate_limit_logger.handler.clear()

        # CReate a file handler for rate limiting logs:
        log_file_path = os.path.join(log_dir, 'rate_limiting.log')
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)

        #Create a formatter
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)

        # Add handler to logger
        self.rate_limi_logger.addHandler(file_handler)
        self.rate_limit_logger.propagate = False

    def __call__(self, request):
        """
        Check if the request is a POST something for sending messags 
        and that it applies rate limiting based on IP address
        """
        if request.method == 'POST' and self.is_message_endpoint(request.path):
            ip_address = self.get_client_ip(request)
            current_time = timezone.now()

            # check if the IP has exceeded rate limit
            if self.is_rate_limited(ip_address, current_time):
                self.log_rate_limit_violation(ip_address, request) # Log the rate limitting event

                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': f'You can only send {self.max_messages} messages per minutes',
                    'limit': self.max_messages,
                    'window': f"{self.time_window} seconds",
                    'retry_after': self.get_retry_after_time(ip_address, current_time),
                    'ip_address': ip_address
                }, status = 429)
            
            # Record the message attempt
            self.record_message_attempt(ip_address, current_time)

        # Continue to the next middleware/view
        response = self.get_response (request)
        return response
    
    def is_message_endpoint(self, path):
        """
        Check if the request path is sending messages
        
        Args:
        path(str): Request path
        Returns:
        bool: True if the path is a message endpoint and false when it's not
        """

        message_endpoints = {
            '/api/messages',
            '/api/conversations',
        }
        # Check for mesage creation endpoints
        for endpoint in message_endpoints:
            if path.startswith(endpoint):
                return True
            
        # Check for nested message endpoints like api/conversations{id}/messages/
        if '/messages/' in path and '/api/' in path:
            return True
        
        return False
    def get_client_ip(self, request):
        """
        Get the clients IP address from the message
        Args: 
            requests: Djangp request object
        Response:
            str: Clients IP address
        """
        x_forwaded_for = request.META.get('HTTP_X_FORWADED_FOR')
        if x_forwaded_for: 
            ip = x_forwaded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'
    
    def is_rate_limited(self, ip_address, current_time):
        """
        Check if the IP has exceeded the rate limit
        Args:
            ip_address(str): Client ip_addeess
            current-time(datetime): Current timestamp
        """
        message_times = self.ip_messages_times[ip_address]

        # Remove old timestamp outside the time window
        cutoff_time = current_time - timedelta(seconds= self.time_window)
        while message_times and message_times[0] < cutoff_time:
            message_times.popleft()

        # Check if the current number of messages exceeds the limit
        return len(message_times) >= self.max_messages
    def record_message_attempt(self, ip_address, current_time):
        """
        Record a message attempt for a given ip_address
        Args:
            ip_address (str): ip_address
            current_time: current timestamp
        """
        message_times = self.ip_message_times[ip_address]
        message_times.append(current_time)

        #Keep only recent timestamp
        cutoff_time = current_time - timedelta(second = self.time_window)
        while message_times and message_times[0] < cutoff_time:
            message_times.popleft()

        # Log the message attempt
        user = getattr(request, 'user', None)
        user_info = user.username if user and user.is_authenticated else 'Anonymous'

        self.rate_limit_logger.info(
            f"{current_time} - IP: {ip_address} - User:{user_info} -"
            f"Message attempt recorded ({len(message_times)}/{self.max_messages})"
        )

    def get_retry_after_time(self,ip_address, current_time):
        """
        Calculate how long the client should wait before making another message request
        Args:
            ip_address(str): Client IP address
            current_time (datetime): Current timestamp
        Returns:
            int: Seconds to wait before retry
        """
        message_times = self.ip_message_times[ip_address]
        if not message_times:
            return 0
        
        #Calculate when the oldest message in the window will expire
        oldest_message_time = message_times[0]
        expiry_time = oldest_message_time + timedelta(seconds=self.time.window)
        retry_after = (expiry_time - current_time).total_seconds()
        
        return max(0, int(retry_after))
    
    def log_rate_limit_violation(self, ip_address,request):
        """
        Log when ab IP address exceeds the rate limit

        Args:
            ip_addres(str): Client ip_address
            request: Django request object
        """
        user = getattr(request, 'user', None)
        user_info = user.username if user and user.is_authenticated else 'Anonymous'
        
        self.rate_limit_logger.info(
            f"{timezone.now()} - RATE LIMIT EXCEEDED - IP ADDRESS:{ip_address} -"
            f"User: {user_info} - Path:{request.path} - Method{request.method}"
        )
