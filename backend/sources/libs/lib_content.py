"""
Content

This class provides extensibility for scraping additional content from URLs stored in the database. It allows adding new methods to retrieve additional content information for a given URL. The results of the content scraping are stored as JSON objects in the database.

Methods:
    __init__(): Initializes the Content object.
    __del__(): Destructor for the Content object.
    get_ipinfo(ip_address): Retrieves additional information using the ipinfo.io service based on the IP address of a URL.

Example:
    content = Content()
    ip_info = content.get_ipinfo(ip_address)
    del content
"""

#load required libs
import ipinfo

class Content:

    def __init__(self):
        self = self

    def __del__(self):
        print('Content object destroyed')

    def get_ipinfo(self, ip_address):
        """
        Custom function to use the [https://ipinfo.io/](https://ipinfo.io/developers) service to gather additional information according to the ip-adress of an URL
        """
        access_token = 'eccc71d7f5f381'
        handler = ipinfo.getHandler(access_token)
        details = handler.getDetails(ip_address)
        return details.all
