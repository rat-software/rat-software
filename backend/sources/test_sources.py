"""
Test script for implementing undetected Chromedriver using SeleniumBase.
For more information, visit: https://github.com/ultrafunkamsterdam/undetected-chromedriver
"""


# Import custom libraries
from libs.lib_sources import Sources

if __name__ == "__main__":
    url = "https://stahlschlag.de"
    sources = Sources()
    print(sources.save_code(url))
