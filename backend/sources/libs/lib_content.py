"""
Extensible class for scraping additional content from URLs stored in the database.
\nIt is possible to add new methods here to get additional content information to a given URL. The results of the content scraping will be stored in JSON-Objects in the database.
\nNew content methods need to be declared here and additional changes at `sources.libs.lib_sources` have to be made to implement the extension of the content dictionary. It is necessary to customize the internal function save_content(attr) and to extend the dictionary like that:
```
attr = {"additional_content":value_to_process} #Definition of key and value for the dictionary
content_value = save_content(attr)
content_dict["additional_content"] = content_value #Store the return value of the save_content(attr)-function
```
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
