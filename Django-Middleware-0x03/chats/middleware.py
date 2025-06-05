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
        self.end_time = time(18,0) # 6 PM



