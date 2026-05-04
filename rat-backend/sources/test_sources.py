#Import custom libraries
from libs.lib_sources import Sources

if __name__ == "__main__":
    url = "https://example.com/" # Replace with the URL you want to scrape
    sources = Sources()
    print(sources.save_code(url))