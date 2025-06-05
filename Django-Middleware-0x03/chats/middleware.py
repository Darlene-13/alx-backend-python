import logging
from datetime import datetime
import os
from django.conf import settings

class ReqquestLoggingMiddleware:
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

        # Configuration of the logger
        self.logger = logging.getLogger('request_logger')
        self.logger.setLevel(logging.INFO)

        # Create a file handler
        log_file = os.path.join(log_dir, 'requests.log')
        file_handler = logging.FileHandler(log_file)

        # Create a formatter
        formatter = logging.Formatter('%(message)s')
        file_handler - logging.FileHandler(log_file)

        #Add handler to logger
        self.logger.addHandler(file_handler)

    def __call__(self, request):
        """"Process the requests and log with the information, this method is called for each request"""
        if request.user.is_authenticated:
            user = request.user.username
        else:
            user = "Anonymous"

        #Log the request information
        log_message = f"{datetime.now()} - User: {user} - Path: {request.path}"
        self.logger.info(log_message)

        #Call the next middleware or view
        response = self.get_response(request)

        return response


