from datetime import datetime
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException, SessionNotCreatedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from seleniumbase import Driver
import uuid
import time
import os
import signal
from functools import wraps
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from urllib.parse import urlsplit, urlparse
import socket
import requests
import base64
from bs4 import BeautifulSoup
import inspect
import http.client
from urllib.parse import urlparse
import urllib.request
import urllib.error

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

# Add a timeout configuration with default of 300 seconds
GLOBAL_TIMEOUT = sources_cnf.get('global_timeout', 300)

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
        # Ensure the screenshot folder exists
        try:
            self.screenshot_folder = os.path.join(parentdir, "tmp")
            os.makedirs(self.screenshot_folder, exist_ok=True)
            print(f"Screenshot folder created/verified: {self.screenshot_folder}")
        except Exception as e:
            # Fallback to current directory if parentdir/tmp fails
            self.screenshot_folder = os.path.join(os.getcwd(), "tmp")
            os.makedirs(self.screenshot_folder, exist_ok=True)
            print(f"Using alternative screenshot folder: {self.screenshot_folder}")
        
    def __del__(self):
        """
        Destructor for the Sources class, called when the object is destroyed.
        """
        print('Sources object destroyed')

    def _cleanup_driver(self, driver):
        """
        Helper method to clean up selenium driver instances
        """
        if driver:
            try:
                driver.close()
            except Exception:
                pass
            try:
                driver.quit()
            except Exception:
                pass

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

    def get_url_header_with_cdp(self, url, driver):
        """
        Nutzt das Chrome DevTools Protocol (CDP), um den Status-Code und Content-Type
        mit dem bestehenden undetected-chromedriver zu bekommen.

        Args:
            url (str): Die URL, für die die Header abgefragt werden sollen.
            driver: Der bestehende Selenium WebDriver.

        Returns:
            dict: Ein Dictionary mit 'content_type' und 'status_code'.
        """

        print("Try to use CDP")
        # Standard-Werte
        content_type = "error"
        status_code = -1

        try:
            # Extrahieren der Hauptdomain für die Filterung
            try:
                meta = self.get_result_meta(url)
                main = meta["main"]
            except Exception:
                main = url

            # Aktivieren des CDP Netzwerk-Monitorings
            try:
                driver.execute_cdp_cmd("Network.enable", {})
            except Exception:
                # Möglicherweise ist CDP bereits aktiviert
                pass

            # Sammeln der Netzwerkantworten
            driver.execute_script("""
                window._networkResponses = [];
                
                // Überwachen der Netzwerkantworten über CDP
                window._responseListener = function(params) {
                    window._networkResponses.push({
                        url: params.response.url,
                        status: params.response.status,
                        contentType: params.response.headers['content-type']
                    });
                };
            """)

            # Ereignis-Handler über CDP hinzufügen
            try:
                # Ereignislistener für Network.responseReceived hinzufügen
                driver.execute_cdp_cmd("Network.responseReceived", {
                    "add": True,
                    "callback": "window._responseListener"
                })
            except Exception as e:
                # Direkte CDP-Ereignisregistrierung fehlgeschlagen, 
                # aber wir können trotzdem weitermachen, da wir möglicherweise 
                # bereits Daten haben
                pass

            # Kurz warten, um Antworten zu sammeln
            time.sleep(1)

            # Antworten abrufen
            responses = driver.execute_script("""
                return window._networkResponses || [];
            """)

            # Die relevante Antwort finden
            if responses:
                for response in responses:
                    if url == response.get('url') or main in response.get('url'):
                        status_code = response.get('status', -1)
                        content_type = response.get('contentType', '')
                        if status_code == 200:
                            break

            # Wenn wir immer noch keinen Status haben, aus den Performance-Einträgen versuchen
            if status_code == -1:
                perf_entries = driver.execute_script("""
                    return window.performance.getEntries().map(e => {
                        return {
                            url: e.name,
                            responseStatus: e.responseStatus,
                            initiatorType: e.initiatorType
                        };
                    });
                """)
                
                for entry in perf_entries:
                    if url == entry.get('url') or main in entry.get('url'):
                        status_code = entry.get('responseStatus', -1)
                        if status_code > 0:
                            break
                    
            # Wenn kein Status gefunden wurde, aber die Seite geladen wurde, 200 annehmen
            if status_code == -1 and driver.page_source and len(driver.page_source) > 100:
                status_code = 200

            # Content-Type erraten, wenn nicht gefunden
            if not content_type or content_type == '':
                # Basierend auf Dokumenttyp
                is_html = driver.execute_script(
                    "return document && document.doctype && document.doctype.name === 'html';"
                )
                if is_html:
                    content_type = "text/html"
                # Basierend auf URL-Endung
                elif url.lower().endswith('.pdf'):
                    content_type = "application/pdf"
                elif url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    content_type = f"image/{url.split('.')[-1].lower()}"
                elif url.lower().endswith(('.mp4', '.avi', '.mov')):
                    content_type = "video/mp4"
                else:
                    # Standardmäßig HTML annehmen
                    content_type = "text/html"

        except Exception as e:
            print(f"CDP header detection failed: {e}")
            # Fallback zur originalen get_url_header Methode
            pass

        print(status_code)
        
        if status_code == -1 or status_code == 0:
            print("Versuche normale get_url_header")
            return self.get_url_header(url, driver)

        # Content-Type normalisieren
        if content_type and ("binary" in content_type or "json" in content_type or "plain" in content_type):
            content_type = "html"
        elif not content_type:
            content_type = "error"

        # PDF anhand von URL erkennen
        if '.pdf' in url.lower() or '?pdf' in url.lower():
            content_type = "pdf"

        # Status-Code normalisieren
        if status_code == 302:
            status_code = 200
        if 200 < status_code < 300:
            status_code = 200

        return {"content_type": content_type, "status_code": status_code}

    def get_url_header(self, url, driver):
        """
        Retrieves the HTTP headers and status code for a given URL.
        Tries multiple methods in sequence until successful.

        Args:
            url (str): The URL to retrieve headers for.
            driver (webdriver): The Selenium WebDriver instance.

        Returns:
            dict: A dictionary containing 'content_type' and 'status_code'.
        """
        # Default values
        content_type = "error"
        status_code = -1

        # Method 1: Try with http.client
        print("Trying http.client")
        try:
            
            parsed_url = urlparse(url)
            connection_type = http.client.HTTPSConnection if parsed_url.scheme == 'https' else http.client.HTTPConnection
            hostname = parsed_url.netloc
            
            path = parsed_url.path if parsed_url.path else '/'
            if parsed_url.query:
                path += '?' + parsed_url.query
            
            conn = connection_type(hostname)
            conn.request("GET", path)
            response = conn.getresponse()
            status_code = response.status
            content_type = response.getheader('Content-Type', '')
            conn.close()
        except Exception as e:
            print(f"Fehler bei der Verbindung: {e}")
            print("Trying urllib")
            

        # Method 2: Try with urllib if Method 1 didn't return a valid status
        if status_code not in [200, 302]:
            try:
                connection = urllib.request.urlopen(url)
                status_code = connection.getcode()
                content_type = connection.info().get('Content-Type', '')
            except urllib.error.HTTPError as e:
                status_code = e.code
                content_type = e.headers.get('Content-Type', '')
            except Exception as e:
                print(f"Fehler bei der Verbindung: {e}")
                print("Trying requests")

        # Method 3: Try with requests if previous methods failed
        if status_code not in [200, 302]:
            try:
                # Extract main domain for filtering
                try:
                    meta = self.get_result_meta(url)
                    main = meta["main"]
                except Exception:
                    main = ""

                # Use requests (GET)
                try:
                    response = requests.get(url, verify=False, timeout=10, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
                    })
                    status_code = response.status_code
                
                    # Try to get Content-Type with HEAD request
                    try:
                        headers = requests.head(url, timeout=3).headers
                        content_type = headers.get('Content-Type', "")
                    except Exception:
                        # If HEAD request fails, guess Content-Type from HTML tags
                        if any(tag in response.text.lower() for tag in ["!doctype html", "/html>"]):
                            content_type = "html"
                            
                except Exception:
                    # Guess mime-type from file extension
                    import mimetypes
                    mt = mimetypes.guess_type(url)
                    if mt and mt[0]:
                        content_type = mt[0]
                    print("Try method existing driver")

                # Method 4: Try to use the existing driver if it's available and previous methods failed
                if status_code not in [200, 302] and driver:
                    try:
                        # Enable CDP network listening on the existing driver
                        try:
                            driver.execute_cdp_cmd("Network.enable", {})
                        except Exception:
                            # CDP might already be enabled, continue
                            pass
                        
                        # Try to directly extract content-type from page
                        try:
                            # Check if we can get the status directly
                            js_status = driver.execute_script(
                                "return window.performance.getEntries().filter(e => e.name === arguments[0])[0].responseStatus || 200;", 
                                url
                            )
                            if js_status:
                                status_code = js_status
                                
                            # Determine content type by checking document structure
                            is_html = driver.execute_script(
                                "return document && document.doctype && document.doctype.name === 'html';"
                            )
                            if is_html:
                                content_type = "text/html"
                                status_code = 200  # If we have HTML content, we can assume 200
                        except Exception:
                            # Script execution failed, try other methods
                            pass
                            
                        # If content type still not determined, make educated guess based on URL
                        if content_type == "error":
                            if url.lower().endswith('.pdf') or '?pdf' in url.lower():
                                content_type = "application/pdf"
                            elif url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                                content_type = f"image/{url.split('.')[-1].lower()}"
                            elif url.lower().endswith(('.mp4', '.avi', '.mov')):
                                content_type = "video/mp4"
                            else:
                                # Default to HTML if we can't determine
                                content_type = "text/html"
                                
                        # If we have page content but no status code, assume 200
                        if status_code == -1 and driver.page_source and len(driver.page_source) > 100:
                            status_code = 200
                        
                    except Exception as e:
                        print(f"Driver-based content type detection failed: {e}")
            except Exception as e:
                print(f"Request methods failed: {e}")

        # Normalize content type and adapt for specific cases
        if content_type and ("binary" in content_type or "json" in content_type or "plain" in content_type):
            content_type = "html"
        elif not content_type:
            content_type = "error"

        # Detect PDF based on URL
        if '.pdf' in url.lower() or '?pdf' in url.lower():
            content_type = "pdf"

        # Normalize status code
        if status_code == 302:
            status_code = 200
        if 200 < status_code < 300:
            status_code = 200

        return {"content_type": content_type, "status_code": status_code}
    
    def get_pdf(self, url):
        """
        Downloads a PDF file from a URL and encodes it in Base64.

        Args:
            url (str): The URL of the PDF file.

        Returns:
            bytes: The Base64 encoded PDF file content.
        """
        pdf_file = os.path.join(self.screenshot_folder, f"{uuid.uuid1()}.pdf")
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
            scroll_time_in_seconds = min(sources_cnf.get('scroll-time', 1), 0.5)  # Limit scroll time for safety
            scrolling = []

            # Calculate maximum time we should spend scrolling (not more than 15% of global timeout)
            max_scroll_time = GLOBAL_TIMEOUT * 0.15
            start_scroll_time = time.time()

            while current_height < height and current_height < sources_cnf.get('max-height', 2000):
                # Check if we're approaching the time limit
                if (time.time() - start_scroll_time) > max_scroll_time:
                    break
                
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
            # Check if we have enough time for scrolling
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

    def save_code(self, url, proxy=None, country_code=None, timeout=None):
        """
        Main method to save the content from a URL with a global timeout.

        Args:
            url (str): The URL to scrape.
            proxy (str, optional): Proxy to use for the request. Defaults to None.
            country_code (str, optional): Country code for locale settings. Defaults to None.
            timeout (int, optional): Custom timeout in seconds. If None, uses GLOBAL_TIMEOUT.

        Returns:
            dict: A dictionary containing the page content, screenshot, metadata, and any error codes.
        """
        # Use custom timeout if provided, otherwise use GLOBAL_TIMEOUT
        actual_timeout = timeout if timeout is not None else GLOBAL_TIMEOUT
        
        # Track the start time immediately
        start_time = time.time()
        
        # Safety check for URL format
        if not url.startswith(('http://', 'https://')):
            return {
                "code": "error", 
                "bin": "", 
                "request": {"content_type": "error", "status_code": -1}, 
                "final_url": url, 
                "meta": {"ip": "-1", "main": url}, 
                "error_codes": "Invalid URL format", 
                "content_dict": {"":""},
                "execution_time": 0
            }
                
        # Use ThreadPoolExecutor with timeout for the entire function
        # This is the most reliable way to enforce timeouts in Python
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._save_code_worker, url, proxy, country_code, start_time, actual_timeout)
            try:
                # The key is to firmly enforce the timeout here with future.result()
                result = future.result(timeout=actual_timeout)
                # Add execution time to the result
                result["execution_time"] = time.time() - start_time
                return result
            except FutureTimeoutError as e:
                # Handle timeout exception
                elapsed_time = time.time() - start_time
                print(f"Scraping timed out after {elapsed_time:.2f} seconds for URL: {url}")
                
                # Attempt to forcefully cancel the future
                future.cancel()
                
                # Return error information
                return {
                    "code": "error", 
                    "bin": "", 
                    "request": {"content_type": "error", "status_code": -1}, 
                    "final_url": url, 
                    "meta": {"ip": "-1", "main": url}, 
                    "error_codes": f"Execution timed out after {elapsed_time:.2f} seconds (limit: {actual_timeout}s)", 
                    "content_dict": {"":""},
                    "execution_time": elapsed_time
                }
            except Exception as e:
                # Handle any other exceptions that might occur
                elapsed_time = time.time() - start_time
                print(f"Error during scraping: {str(e)}")
                return {
                    "code": "error", 
                    "bin": "", 
                    "request": {"content_type": "error", "status_code": -1}, 
                    "final_url": url, 
                    "meta": {"ip": "-1", "main": url}, 
                    "error_codes": f"Error: {str(e)} after {elapsed_time:.2f}s", 
                    "content_dict": {"":""},
                    "execution_time": elapsed_time
                }

    def _save_code_worker(self, url, proxy=None, country_code=None, start_time=None, timeout=GLOBAL_TIMEOUT):
        """
        Worker method that performs the actual scraping within the timeout boundary.
        
        Args:
            url (str): The URL to scrape.
            proxy (str, optional): Proxy to use for the request. Defaults to None.
            country_code (str, optional): Country code for locale settings. Defaults to None.
            start_time (float, optional): Time when the operation started. Used for timeout checks.
            timeout (int, optional): Timeout in seconds.
                    
        Returns:
            dict: A dictionary containing the page content, screenshot, metadata, and any error codes.
        """
        if "#:~:text=" in url:
            url = url.split("#:~:text=")[0]

        error_codes = ""
        code = "error"  # Default to error in case of timeout
        bin_data = ""
        dict_request = {"content_type": "error", "status_code": -1}
        final_url = url
        meta = {"ip": "-1", "main": url}
        content_dict = {"":""}
        driver = None
        
        # Use provided start_time or create a new one
        if start_time is None:
            start_time = time.time()
        
        # Add inner timeout checker that can be used throughout the function
        def check_remaining_time():
            """Check if we're out of time and should abort processing"""
            elapsed = time.time() - start_time
            return elapsed > timeout * 0.95  # 95% of timeout used
        
        # Function to check if we're approaching timeout
        def check_timeout(percentage, operation_name=""):
            elapsed = time.time() - start_time
            if elapsed > timeout * percentage:
                nonlocal error_codes
                message = f"Approaching timeout limit ({elapsed:.2f}s / {timeout}s) at {percentage*100}%"
                if operation_name:
                    message += f", during {operation_name}"
                error_codes += message + "; "
                print(message)
                return True
            return False
            
        # Set page load timeout to be much shorter than our total timeout
        # This ensures the driver doesn't hang too long on any single page load
        page_load_timeout = min(30, timeout * 0.3)

        # Regular periodic timeout check
        if check_timeout(0.05, "initial setup"):
            return {"code": "error", "bin": "", "request": dict_request, "final_url": url, 
                "meta": meta, "error_codes": error_codes, "content_dict": content_dict}
        
        # Configure Driver with appropriate settings
        driver_options = {
            "browser": "chrome",
            "wire": True,
            "uc": True,
            "headless2": headless,
            "incognito": False,
            "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "do_not_track": True,
            "undetectable": True,
            "no_sandbox": True
        }
        
        # Only add extension if it exists
        if os.path.exists(ext_path):
            driver_options["extension_dir"] = ext_path
        
        if proxy:
            driver_options["proxy"] = proxy

        if country_code:
            driver_options["locale_code"] = country_code
            
        # Check if we've already used too much time before even starting the driver
        if check_timeout(0.1, "pre-driver initialization"):
            return {"code": "error", "bin": "", "request": dict_request, "final_url": url, 
                "meta": meta, "error_codes": error_codes, "content_dict": content_dict}
                    
        # Driver initialization with timeout
        try:
            # Create the driver with a timeout for its creation
            MAX_DRIVER_INIT_TIME = min(60, timeout * 0.2)  # 20% of total timeout or 60s max
            driver_init_start = time.time()
            
            # Set a timeout for driver initialization
            def init_driver():
                return Driver(**driver_options)
            
            with ThreadPoolExecutor(max_workers=1) as executor:
                future_driver = executor.submit(init_driver)
                try:
                    driver = future_driver.result(timeout=MAX_DRIVER_INIT_TIME)
                except Exception as e:
                    error_codes += f"Driver initialization timeout after {time.time() - driver_init_start:.2f}s: {str(e)}; "
                    return {"code": "error", "bin": "", "request": dict_request, "final_url": url, 
                        "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

            # Check if we're out of time after driver init
            if check_remaining_time():
                error_codes += "Timeout after driver initialization; "
                self._cleanup_driver(driver)
                return {"code": "error", "bin": "", "request": dict_request, "final_url": url, 
                    "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

            if proxy:
                print(f"Using proxy {proxy} for scraping {url}")
            else:
                print(f"Direct connection (no proxy) for scraping {url}")

            # Set timeouts aggressively to prevent hanging
            driver.set_page_load_timeout(page_load_timeout)
            driver.set_script_timeout(min(10, page_load_timeout * 0.5))
            driver.implicitly_wait(min(5, timeout * 0.1))  # Very short implicit wait
            
            # Enable CDP network monitoring right after driver creation
            try:
                driver.execute_cdp_cmd("Network.enable", {})
            except Exception as e:
                print(f"CDP Network enable failed: {e}")
                
        except Exception as e:
            error_codes += f"Driver initialization failed: {e}; "
            return {"code": "error", "bin": "", "request": dict_request, "final_url": url, 
                "meta": meta, "error_codes": error_codes, "content_dict": content_dict}
        
        # Check timeout after driver initialization
        if check_timeout(0.3, "driver initialization"):
            if driver:
                self._cleanup_driver(driver)
            return {"code": "error", "bin": "", "request": dict_request, "final_url": url, 
                "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

        # Set up the page load with its own timeout
        page_load_success = False
        try:
            # Use a more defensive page loading approach with a separate thread
            def load_page():
                nonlocal driver
                driver.get(url)
                return True
                
            with ThreadPoolExecutor(max_workers=1) as page_executor:
                page_future = page_executor.submit(load_page)
                try:
                    page_load_success = page_future.result(timeout=page_load_timeout)
                except Exception as e:
                    error_codes += f"Page load timeout: {str(e)}; "
                    # Continue with what we have
            
            # Calculate safe wait time based on remaining time
            safe_wait_time = min(sources_cnf.get('wait_time', 3), timeout * 0.05)
            
            # Only wait if we have enough time and page loading was at least attempted
            if not check_timeout(0.5, "page loading"):
                time.sleep(safe_wait_time)
                
        except Exception as e:
            error_codes += f"URL unreachable: {e}; "
            if driver:
                self._cleanup_driver(driver)
            return {"code": "error", "bin": "", "request": dict_request, "final_url": url, 
                "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

        # Forced timeout check - if we're approaching timeout, return what we have
        if check_remaining_time():
            error_codes += "Timeout after page load; "
            if driver:
                try:
                    # Try to get at least something before cleanup
                    try:
                        code = driver.page_source
                    except:
                        pass
                    self._cleanup_driver(driver)
                except:
                    pass
            result_dict = {
                "code": code if code and code != "error" else "error",
                "bin": bin_data,
                "request": dict_request,
                "final_url": final_url,
                "meta": meta,
                "error_codes": error_codes + " Forced early return due to timeout; ",
                "content_dict": content_dict
            }
            return result_dict

        # Header retrieval with timeout
        try:
            # Check timeout before proceeding with header retrieval
            if check_timeout(0.6, "before header retrieval"):
                dict_request = {"content_type": "error", "status_code": -1}
            else:
                # Use CDP-based header detection with its own timeout
                header_start = time.time()
                MAX_HEADER_TIME = min(20, timeout * 0.15)  # 15% of total or 20s max
                
                def get_headers():
                    return self.get_url_header_with_cdp(url, driver)
                
                with ThreadPoolExecutor(max_workers=1) as header_executor:
                    header_future = header_executor.submit(get_headers)
                    try:
                        dict_request = header_future.result(timeout=MAX_HEADER_TIME)
                    except Exception as e:
                        error_codes += f"Header retrieval timeout after {time.time() - header_start:.2f}s: {str(e)}; "
                        dict_request = {"content_type": "error", "status_code": -1}
                
        except Exception as e:
            dict_request = {"content_type": "error", "status_code": -1}
            error_codes += f"Header retrieval failed: {e}; "

        # Another forced timeout check
        if check_remaining_time():
            error_codes += "Timeout after header retrieval; "
            if driver:
                self._cleanup_driver(driver)
            return {"code": "error", "bin": "", "request": dict_request, "final_url": url, 
                "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

        # Main content processing
        try:
            if dict_request["status_code"] == 200:
                try:
                    code = driver.page_source
                    
                    if not code or code == '' or len(code) == 0:
                        code = "error"
                        error_codes += "Empty page source; "

                    try:
                        if "http" in driver.current_url:
                            final_url = driver.current_url
                        else:
                            final_url = url
                    except Exception:
                        final_url = url

                    try:
                        meta = self.get_result_meta(final_url)
                    except Exception as e:
                        error_codes += f"Get result meta failed: {e}; "

                except TimeoutException:
                    try:
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                    except Exception as e:
                        code = "error"
                        error_codes += f"Timeout: {e}; "

                # Final timeout check before heavy operations
                if check_remaining_time():
                    error_codes += "Timeout before content processing; "
                    if driver:
                        self._cleanup_driver(driver)
                    return {"code": code if code and code != "error" else "error", 
                            "bin": bin_data,
                            "request": dict_request, 
                            "final_url": final_url, 
                            "meta": meta, 
                            "error_codes": error_codes, 
                            "content_dict": content_dict}

                if code != "error":
                    # Check timeout before heavy operations
                    if check_timeout(0.7, "before processing content"):
                        code = "error"
                    elif "pdf" in dict_request["content_type"]:
                        try:
                            # Use a timeout for PDF download
                            MAX_PDF_TIME = min(30, timeout * 0.2)
                            pdf_start = time.time()
                            
                            def get_pdf_data():
                                return self.get_pdf(url)
                            
                            with ThreadPoolExecutor(max_workers=1) as pdf_executor:
                                pdf_future = pdf_executor.submit(get_pdf_data)
                                try:
                                    bin_data = pdf_future.result(timeout=MAX_PDF_TIME)
                                    code = "pdf"
                                except Exception as e:
                                    error_codes += f"PDF download timeout after {time.time() - pdf_start:.2f}s: {str(e)}; "
                                    code = "error"
                                    
                        except Exception as e:
                            code = "error"
                            error_codes += f"PDF download failed: {e}; "
                    else:
                        try:
                            # Calculate safe wait time based on remaining time
                            remaining_time = timeout - (time.time() - start_time)
                            safe_wait_time = min(sources_cnf.get('wait_time', 3), remaining_time * 0.05)
                            
                            if remaining_time > 10:  # Only wait if we have enough time
                                time.sleep(safe_wait_time)
                            
                            # Only take screenshot if we have enough time
                            if check_timeout(0.8, "before screenshot"):
                                code = "error"
                            else:
                                # Use a timeout for screenshot
                                MAX_SCREENSHOT_TIME = min(30, timeout * 0.15)
                                screenshot_start = time.time()
                                
                                def take_screenshot_with_timeout():
                                    return self.take_screenshot(driver)
                                
                                with ThreadPoolExecutor(max_workers=1) as screenshot_executor:
                                    screenshot_future = screenshot_executor.submit(take_screenshot_with_timeout)
                                    try:
                                        bin_data = screenshot_future.result(timeout=MAX_SCREENSHOT_TIME)
                                        code = self.encode_code(code)
                                        dict_request["content_type"] = "html"
                                    except Exception as e:
                                        error_codes += f"Screenshot timeout after {time.time() - screenshot_start:.2f}s: {str(e)}; "
                                        # Still try to encode the code even if screenshot fails
                                        try:
                                            code = self.encode_code(code)
                                            dict_request["content_type"] = "html"
                                        except:
                                            code = "error"
                                
                        except Exception as e:
                            code = "error"
                            error_codes += f"Screenshot / HTML failed: {e}; "
                else:
                    code = "error"
                    error_codes += f"Invalid page content; "
            else:
                code = "error"
                error_codes += f"Wrong status code: {dict_request['status_code']}; "

        except Exception as e:
            error_codes += f"Content processing failed: {e}; "
            code = "error"
        finally:
            # Always clean up the driver at the end of processing
            if driver:
                self._cleanup_driver(driver)

        # Final check if we've exceeded our time limit
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            error_codes += f"Process exceeded the timeout limit of {timeout} seconds (took {elapsed_time:.2f}s); "
            code = "error"

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