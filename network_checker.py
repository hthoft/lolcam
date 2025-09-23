import socket
import logging

class InternetChecker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def check_internet(self):
        """
        Simple one-time internet check.
        Returns True if connected, False otherwise.
        """
        try:
            socket.setdefaulttimeout(5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('8.8.8.8', 53))
            self.logger.info("Internet connection verified")
            return True
        except Exception as e:
            self.logger.warning(f"No internet connection: {e}")
            return False
