from datetime import datetime
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from seleniumbase import Driver
import uuid
import time
import os
from urllib.parse import urlsplit, urlparse
import socket
import requests
import base64
from bs4 import BeautifulSoup
import inspect

# Define the path for configurations and extensions
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)
ext_path = os.path.join(parentdir, "i_care_about_cookies_unpacked")




from libs.lib_helper import Helper
from libs.lib_content import Content

# Initialize the Helper instance
helper = Helper()

# Load configuration from file
sources_cnf = helper.file_to_dict(os.path.join(parentdir, 'config/config_sources.ini'))


# Determine whether to run in headless mode
headless = sources_cnf.get('headless')

if headless == 1:
    headless = True
else:
    headless = False



del helper

class Sources:
    """
    A class to handle web scraping tasks, including saving webpage content,
    taking screenshots, and handling PDF files.
    """

    def __init__(self):
        """
        Initializes the Sources instance.
        """
        # Initialization logic if needed
        pass

    def __del__(self):
        """
        Destructor for the Sources class, called when the object is destroyed.
        """
        print('Sources object destroyed')

    def encode_code(self, code):
        """
        Encodes a string into Base64 format.

        Args:
            code (str): The string to be encoded.

        Returns:
            bytes: The Base64 encoded string.
        """
        return base64.b64encode(code.encode('utf-8', 'ignore'))

    def decode_code(self, code):
        """
        Decodes a Base64 encoded string and beautifies the HTML content.

        Args:
            code (bytes): The Base64 encoded string.

        Returns:
            str: The beautified HTML content.
        """
        code_decoded = base64.b64decode(code)
        soup = BeautifulSoup(code_decoded, "html.parser")
        return str(soup)

    def encode_file_base64(self, file):
        """
        Encodes a file's content into Base64 format.

        Args:
            file (str): The path to the file to be encoded.

        Returns:
            bytes: The Base64 encoded file content.
        """
        with open(file, 'rb') as f:
            return base64.b64encode(f.read())

    def get_result_meta(self, url):
        """
        Retrieves metadata for a given URL, including IP address and main URL.

        Args:
            url (str): The URL to retrieve metadata for.

        Returns:
            dict: A dictionary containing 'ip' and 'main' URL.
        """
        meta = {}
        try:
            parsed_uri = urlparse(url)
            hostname = parsed_uri.netloc
            ip = socket.gethostbyname(hostname)
        except Exception:
            ip = "-1"

        try:
            main = f'{parsed_uri.scheme}://{parsed_uri.netloc}/'
        except Exception:
            main = url

        meta = {"ip": ip, "main": main}
        return meta

    def get_url_header(self, url, driver):
        """
        Retrieves the HTTP headers and status code for a given URL.

        Args:
            url (str): The URL to retrieve headers for.
            driver (webdriver): The Selenium WebDriver instance.

        Returns:
            dict: A dictionary containing 'content_type' and 'status_code'.
        """
        try:
            meta = self.get_result_meta(url)
            main = meta["main"]
        except Exception:
            main = ""

        content_type = ""
        status_code = -1

        try:
            response = requests.get(url, verify=False, timeout=10, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
            })
            status_code = response.status_code
           
            try:
                headers = requests.head(url, timeout=3).headers
                content_type = headers.get('Content-Type', "")
            except Exception as e:
                if any(tag in response.text.lower() for tag in ["!doctype html", "/html>"]):
                    content_type = "html"

        except Exception:
            import mimetypes
            mt = mimetypes.guess_type(url)
            if mt:
                content_type = mt[0]

        if status_code in [302, 403]:
            status_code = 200

        if status_code not in [200, -1]:
            try:
                for request in driver.requests:
                    if main in request.url:
                        status_code = request.response.status_code
                        content_type = request.response.headers.get('Content-Type', "")
                        if status_code in [200, 302]:
                            break
            except Exception as e:
                print(str(e))

        if not content_type:

            if "binary" in content_type or "json" in content_type or "plain" in content_type:
                content_type = "html"

            else:
                content_type = "error"

        return {"content_type": content_type, "status_code": status_code}

    def get_pdf(self, url):
        """
        Downloads a PDF file from a URL and encodes it in Base64.

        Args:
            url (str): The URL of the PDF file.

        Returns:
            bytes: The Base64 encoded PDF file content.
        """
        pdf_file = f"{uuid.uuid1()}.pdf"
        response = requests.get(url, allow_redirects=True)
        with open(pdf_file, 'wb') as f:
            f.write(response.content)
        bin_data = self.encode_file_base64(pdf_file)
        os.remove(pdf_file)
        return bin_data

    def take_screenshot(self, driver):
        """
        Takes a screenshot of the current webpage.

        Args:
            driver (webdriver): The Selenium WebDriver instance.

        Returns:
            bytes: The Base64 encoded screenshot image.
        """
        def simulate_scrolling(driver, required_height):
            """
            Scrolls the webpage to the specified height.

            Args:
                driver (webdriver): The Selenium WebDriver instance.
                required_height (int): The height to scroll to.

            Returns:
                list: The driver and the required height after scrolling.
            """
            height = required_height
            current_height = 0
            block_size = sources_cnf.get('block-size', 100)
            scroll_time_in_seconds = sources_cnf.get('scroll-time', 1)
            scrolling = []

            while current_height < height and current_height < sources_cnf.get('max-height', 2000):
                current_height += block_size
                scroll_to = f"window.scrollTo(0,{current_height})"
                driver.execute_script(scroll_to)
                height = driver.execute_script('return document.body.parentNode.scrollHeight')
                time.sleep(scroll_time_in_seconds)

            driver.execute_script("window.scrollTo(0,1)")
            required_height = driver.execute_script('return document.body.parentNode.scrollHeight')
            scrolling = [driver, required_height]
            return scrolling

        screenshot_folder = os.path.join(parentdir, "tmp")
        screenshot_file = os.path.join(screenshot_folder, f"{uuid.uuid1()}.png")

        driver.maximize_window()  # Maximize browser window for screenshot
        required_height = driver.execute_script('return document.body.parentNode.scrollHeight')

        try:
            driver.execute_script("window.scrollTo(0,1)")
        except Exception:
            pass

        try:
            scrolling = simulate_scrolling(driver, required_height)
            driver = scrolling[0]
            required_height = scrolling[1]
        except Exception as e:
            print(str(e))

        try:
            driver.execute_script("window.scrollTo(0,1)")
        except Exception:
            pass

        try:
            required_width = driver.execute_script('return document.body.parentNode.scrollWidth')
            if required_width < sources_cnf.get('min-width', 1024):
                required_width = sources_cnf.get('min-width', 1024)
            if required_height > sources_cnf.get('max-height', 2000):
                required_height = sources_cnf.get('max-height', 2000)
            required_width = 1024
            driver.set_window_size(required_width, required_height)
            driver.save_screenshot(screenshot_file)
        except Exception:
            driver.save_screenshot(screenshot_file)

        screenshot = self.encode_file_base64(screenshot_file)
        if sources_cnf.get("debug_screenshots", 0) == 0:
            os.remove(screenshot_file)

        return screenshot

    def save_code(self, url):
        """
        Main method to save the content from a URL.

        Args:
            url (str): The URL to scrape.

        Returns:
            dict: A dictionary containing the page content, screenshot, metadata, and any error codes.
        """
        error_codes = ""
        code = ""
        bin_data = ""
        dict_request = {}
        final_url = url
        meta = {"ip": "-1", "main": url}
        content_dict = {"":""}

        try:
            driver = Driver(
                browser="chrome",
                wire=True,
                uc=True,
                headless2=headless,
                incognito=False,
                agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                do_not_track=True,
                undetectable=True,
                extension_dir=ext_path,
                no_sandbox=True,
            )

            driver.set_page_load_timeout(sources_cnf.get('timeout', 30))
            driver.implicitly_wait(60)
            try:
                driver.get(url)
            except Exception as e:
                error_codes += f"URL unreachable: {e}; "
                driver.close()
                driver.quit()
                return {"code": "error", "bin": "", "request": {}, "final_url": url, "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

            try:
                dict_request = self.get_url_header(url, driver)
            except Exception:
                dict_request = {"content_type": "error", "status_code": -1}
                error_codes += "Requests failed"

            if dict_request["status_code"] == 200:
                try:
                    code = driver.page_source
                    if not code:
                        code = "error"

                    try:
                        final_url = driver.current_url
                    except Exception:
                        final_url = url

                    try:
                        meta = self.get_result_meta(final_url)
                    except Exception:
                        error_codes += "Get result meta failed"

                except TimeoutException:
                    try:
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    except Exception as e:
                        code = "error"
                        error_codes += f"Timeout: {e}; "

                if code != "error":
                    if "html" in dict_request["content_type"]:
                        try:
                            time.sleep(sources_cnf.get('wait_time', 2))
                            bin_data = self.take_screenshot(driver)
                            code = self.encode_code(code)
                        except Exception as e:
                            code = "error"
                            error_codes += f"Screenshot failed: {e}; "
                    elif "pdf" in dict_request["content_type"]:
                        try:
                            bin_data = self.get_pdf(url)
                            code = "pdf"
                        except Exception as e:
                            code = "error"
                            error_codes += f"PDF download failed: {e}; "

            driver.close()
            driver.quit()

        except Exception as e:
            error_codes += f"Scraping failed: {e}; "
            try:
                driver.close()
                driver.quit()
            except Exception:
                pass

        result_dict = {
            "code": code,
            "bin": bin_data,
            "request": dict_request,
            "final_url": final_url,
            "meta": meta,
            "error_codes": error_codes,
            "content_dict": content_dict
        }

        return result_dict
