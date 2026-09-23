import base64
import http
import inspect
import io
import json
import os
import socket
import threading
import time
import urllib
import uuid
import zipfile
from urllib.parse import urlparse
from abc import abstractmethod, ABCMeta

import requests
from PIL.Image import Image


class LibScraper(metaclass=ABCMeta):
    def __init__(self):
        # Define the path for configurations and extensions
        self.currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(self.currentdir)
        self.parentdir = os.path.dirname(parentdir)

        rules_path = os.path.abspath(os.path.join(parentdir, "config", "rules.json"))

        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                cookie_rules = json.load(f)
                print(f"{len(cookie_rules)} cookie rules loaded from '{rules_path}'")
        except Exception as e:
            print(f"Warning: rules.json could not be loaded from '{rules_path}' Use the global heuristics. Error: {e}")
            cookie_rules = []

        from libs.lib_helper import Helper

        # Initialize the Helper instance
        helper = Helper()

        try:
            # Load configuration from file
            self.sources_cnf = helper.file_to_dict(os.path.join(parentdir, 'config/config_sources.ini'))

            # Determine whether to run in headless mode
            self.headless = self.sources_cnf.get('headless', True)

            # Add a timeout configuration with default of 300 seconds
            self.GLOBAL_TIMEOUT = self.sources_cnf.get('global_timeout', 300)

            self.API_KEY = self.sources_cnf.get('api-key', '')
            # Safely construct self.STORAGE_URL
            base_storage_url = self.sources_cnf.get('storage-url')
            if base_storage_url:
                self.STORAGE_URL = base_storage_url.rstrip('/') + "/upload"
            else:
                self.STORAGE_URL = None

            self.LOCAL_STORAGE_PATH = self.sources_cnf.get('local-storage-path', None)

        except Exception as e:
            print(
                f"Notice: config_sources.ini missing or incomplete (if you want to use RAT in production you need to setup a rat-storage-server). Running in standalone mode. ({e})")
            # Set safe defaults for testing
            self.headless = True
            self.GLOBAL_TIMEOUT = 300
            self.API_KEY = ""
            self.STORAGE_URL = None
            self.LOCAL_STORAGE_PATH = None
            sources_cnf = {}
        del helper

        # Initializes the Sources instance.

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

    def upload_to_storage(self, html_content, bin_data, content_type):
        zip_filename = f"{uuid.uuid4()}.zip"

        # 1. Create a ZIP file on the device
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            if html_content and isinstance(html_content, str) and html_content != "error":
                zf.writestr('source.html', html_content.encode('utf-8', 'ignore'))

            if bin_data and bin_data != "error":
                # CORRECTION FOR PDF DETECTION
                c_type = str(content_type).lower() if content_type else ""
                filename = 'source.pdf' if "pdf" in c_type else 'screenshot.jpg'
                zf.writestr(filename, bin_data)

        zip_buffer.seek(0)

        # 2. API or LOCAL

        # CASE A: We have configured an API URL -> Attempt upload
        if self.STORAGE_URL and "http" in self.STORAGE_URL:
            try:
                headers = {"X-API-Key": self.API_KEY}
                files = {"file": (zip_filename, zip_buffer, "application/zip")}

                print(f"Trying to upload to API: {self.STORAGE_URL}")
                response = requests.post(self.STORAGE_URL, headers=headers, files=files, timeout=30)

                if response.status_code == 200:
                    remote_filename = response.json().get("filename")
                    print(f"API upload successful: {remote_filename}")
                    return remote_filename
                else:
                    print(f"API upload failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"API Error: {e}")

        # CASE B: No API or upload failed -> Save locally
        try:
            local_storage_path = self.LOCAL_STORAGE_PATH

            # Try main path, fallback to project tmp folder if permission denied
            try:
                os.makedirs(local_storage_path, exist_ok=True)
            except PermissionError:
                local_storage_path = os.path.join(self.parentdir, "tmp", "local_storage")
                os.makedirs(local_storage_path, exist_ok=True)
                print(f"Notice: No access to /var/www/. Saving fallback to {local_storage_path}")

            local_filepath = os.path.join(local_storage_path, zip_filename)

            zip_buffer.seek(0)

            with open(local_filepath, "wb") as f:
                f.write(zip_buffer.read())

            print(f"Saved locally: {local_filepath}")
            return zip_filename

        except Exception as e:
            print(f"Critical error during local saving: {e}")
            return None

    def __del__(self):
        """
        Destructor for the Sources class, called when the object is destroyed.
        """
        print('Sources object destroyed')

    def _cleanup_driver(self, driver):
        if driver:
            try:
                # Force disconnect from DevTools before closing
                try:
                    if hasattr(driver, 'execute_cdp_cmd'):
                        driver.execute_cdp_cmd('Network.disable', {})
                        driver.execute_cdp_cmd('Page.disable', {})
                except:
                    pass

                # Try to terminate all sessions
                try:
                    driver.execute_script('window.onbeforeunload = null;')
                except:
                    pass

                driver.close()
            except:
                pass
            try:
                driver.quit()
            except:
                pass

    def get_result_meta(self, url):
        """
        Retrieves metadata for a URL with maximum data recovery.
        Always attempts to parse the main URL, even if the IP lookup fails.
        """
        # 1. Define default fallback values
        ip = "-1"
        main = url  # If everything goes wrong, the original URL remains
        hostname = None

        # 2. Attempt to extract the main URL
        try:
            parsed_url = urlparse(url)

            if parsed_url.scheme and parsed_url.netloc:
                hostname = parsed_url.netloc
                main = f"{parsed_url.scheme}://{hostname}/"
            else:
                print(f"Parsing Warning: Invalid URL structure for '{url}'. 'main' remains original URL.")
        except Exception as e:
            print(f"Parsing Error for '{url}': {e}. 'main' remains original URL.")
            # Here not to abort, we still have the fallback value for 'main'

        # 3. Attempt to get the IP address, if a hostname was found
        if hostname:
            try:
                ip = socket.gethostbyname(hostname)
            except Exception as e:
                # The IP lookup failed, but 'main' could still be correct
                print(f"DNS Error for host '{hostname}': {e}. IP will be set to '-1'.")
                ip = "-1"

        return {"ip": ip, "main": main}

    def get_url_header_with_cdp(self, url, driver):
        """
        Uses the Chrome DevTools Protocol (CDP) to retrieve the status code and content type
        using the existing undetected-chromedriver.

        Args:
            url (str): The URL for which the headers should be retrieved.
            driver: The existing Selenium WebDriver.

        Returns:
            dict: A dictionary containing ‘content_type’ and ‘status_code’.
        """

        print("Try to use CDP")
        # Standard defaults
        content_type = "error"
        status_code = -1

        try:
            try:
                meta = self.get_result_meta(url)
                main = meta["main"]
            except Exception:
                main = url

            try:
                driver.execute_cdp_cmd("Network.enable", {})

                driver.execute_cdp_cmd('Network.setBlockedURLs', {
                    "urls": [
                        "*cdn.cookielaw.org*",  # OneTrust
                        "*consent.cookiebot.com*",  # Cookiebot
                        "*trustarc.com*",  # TrustArc
                        "*quantcast.com*",  # Quantcast
                        "*usercentrics.eu*",  # Usercentrics
                        "*app.usercentrics.eu*",  # Usercentrics App
                        "*cmp.inmobi.com*",  # InMobi CMP
                        "*sourcepoint.com*",  # Sourcepoint
                        "*cdn.privacy-mgmt.com*",  # Privacy Manager
                        "*cookie-script.com*"  # Cookie-Script
                    ]
                })
                print("CDP: Cookie consent provider successfully blocked.")
            except Exception as e:
                print(f"CDP Network enable/block failed: {e}")

            driver.execute_script("""
                window._networkResponses = [];

                // Monitoring network responses via CDP
                window._responseListener = function(params) {
                    window._networkResponses.push({
                        url: params.response.url,
                        status: params.response.status,
                        contentType: params.response.headers['content-type']
                    });
                };
            """)

            # Add an event handler via CDP
            try:
                # Event listener for Network.responseReceived
                driver.execute_cdp_cmd("Network.responseReceived", {
                    "add": True,
                    "callback": "window._responseListener"
                })
            except Exception as e:
                pass

            time.sleep(1)

            # View replies
            responses = driver.execute_script("""
                return window._networkResponses || [];
            """)

            # Find the relevant answer
            if responses:
                for response in responses:
                    if url == response.get('url') or main in response.get('url'):
                        status_code = response.get('status', -1)
                        content_type = response.get('contentType', '')
                        if status_code == 200:
                            break

            # If we still don't have a status, try checking the performance logs
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

            # If no status was found but the page loaded, return a 200
            if status_code == -1 and driver.page_source and len(driver.page_source) > 100:
                status_code = 200

            # Guess the content type if not found
            if not content_type or content_type == '':
                # Based on document type
                is_html = driver.execute_script(
                    "return document && document.doctype && document.doctype.name === 'html';"
                )
                if is_html:
                    content_type = "text/html"
                # Based on URL extension
                elif url.lower().endswith('.pdf'):
                    content_type = "application/pdf"
                elif url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    content_type = f"image/{url.split('.')[-1].lower()}"
                elif url.lower().endswith(('.mp4', '.avi', '.mov')):
                    content_type = "video/mp4"
                else:
                    # Accept HTML by default
                    content_type = "text/html"

        except Exception as e:
            print(f"CDP header detection failed: {e}")
            # Fallback to the original get_url_header method
            pass

        print(status_code)

        if status_code == -1 or status_code == 0:
            print("Trying normal get_url_header")
            return self.get_url_header(url, driver)

        # Normalize the Content-Type
        if content_type and ("binary" in content_type or "json" in content_type or "plain" in content_type):
            content_type = "html"
        elif not content_type:
            content_type = "error"

        # Identify a PDF by its URL
        if '.pdf' in url.lower() or '?pdf' in url.lower():
            content_type = "pdf"

        # Normalize status code
        if status_code == 302:
            status_code = 200
        if 200 < status_code < 300:
            status_code = 200

        return {"content_type": content_type, "status_code": status_code}

    def get_url_header(self, url, driver):
        """
        Retrieves the HTTP headers and status code for a given URL with proper timeouts.
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

        # Global timeout for the entire function
        start_time = time.time()
        max_total_time = 30  # Max 30 seconds for the whole function

        # Method 1: Try with http.client (with strict timeout)
        print("Trying http.client")
        try:
            # Set socket timeout
            import socket
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(30)  # 30 seconds timeout

            try:
                parsed_url = urlparse(url)
                connection_type = http.client.HTTPSConnection if parsed_url.scheme == 'https' else http.client.HTTPConnection
                hostname = parsed_url.netloc

                path = parsed_url.path if parsed_url.path else '/'
                if parsed_url.query:
                    path += '?' + parsed_url.query

                # Use timeout for connection
                conn = connection_type(hostname, timeout=30)

                # Run request in a thread with timeout
                def make_request():
                    nonlocal status_code, content_type
                    conn.request("GET", path)
                    response = conn.getresponse()
                    status_code = response.status
                    content_type = response.getheader('Content-Type', '')
                    conn.close()

                # Thread with timeout for the request
                request_thread = threading.Thread(target=make_request)
                request_thread.daemon = True
                request_thread.start()
                request_thread.join(30)  # Wait max 10 seconds

                # If thread is still alive after timeout, it's hanging
                if request_thread.is_alive():
                    print("http.client request timed out")
                    try:
                        conn.close()
                    except:
                        pass
                    raise TimeoutError("Connection request timed out")
            finally:
                # Restore original socket timeout
                socket.setdefaulttimeout(original_timeout)
        except Exception as e:
            print(f"Connection error: {e}")
            print("Trying urllib")

        # Check if we're running out of time
        if time.time() - start_time > max_total_time:
            print(f"Header retrieval timeout reached after {time.time() - start_time:.2f}s")
            return {"content_type": content_type, "status_code": status_code}

        # Method 2: Try with urllib if Method 1 didn't return a valid status
        if status_code not in [200, 302]:
            try:
                # Use timeout for urllib
                connection = urllib.request.urlopen(url, timeout=10)
                status_code = connection.getcode()
                content_type = connection.info().get('Content-Type', '')
            except urllib.error.HTTPError as e:
                status_code = e.code
                content_type = e.headers.get('Content-Type', '')
            except Exception as e:
                print(f"Connection error: {e}")
                print("Trying requests")

        # Check if we're running out of time
        if time.time() - start_time > max_total_time:
            print(f"Header retrieval timeout reached after {time.time() - start_time:.2f}s")
            return {"content_type": content_type, "status_code": status_code}

        # Method 3: Try with requests if previous methods failed
        if status_code not in [200, 302]:
            try:
                # Extract main domain for filtering
                try:
                    meta = self.get_result_meta(url)
                    main = meta["main"]
                except Exception:
                    main = ""

                # Use requests (GET) with strict timeout
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

                # Check if we're running out of time before trying driver method
                if time.time() - start_time > max_total_time:
                    print(f"Header retrieval timeout reached after {time.time() - start_time:.2f}s")
                    return {"content_type": content_type, "status_code": status_code}

                # Method 4: Try to use the existing driver if it's available and previous methods failed
                if status_code not in [200, 302] and driver:
                    try:
                        # Enable CDP network listening on the existing driver
                        try:
                            driver.execute_cdp_cmd("Network.enable", {})
                        except Exception:
                            # CDP might already be enabled, continue
                            pass

                        # Try to directly extract content-type from page with timeout
                        try:
                            # Use js_executor with timeout
                            def get_js_results():
                                nonlocal status_code, content_type

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

                            # Run in a thread with timeout
                            js_thread = threading.Thread(target=get_js_results)
                            js_thread.daemon = True
                            js_thread.start()
                            js_thread.join(5)  # Wait max 5 seconds

                            if js_thread.is_alive():
                                print("JavaScript execution timed out")
                                raise TimeoutError("JavaScript timeout")

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

        print(f"Header retrieval completed in {time.time() - start_time:.2f}s with status {status_code}")
        return {"content_type": content_type, "status_code": status_code}

    def get_pdf(self, url, timeout=30):
        """
        Downloads a PDF file from a URL and encodes it in Base64.
        Improved implementation with better error handling and streaming support.

        Args:
            url (str): The URL of the PDF file.
            timeout (int): Timeout in seconds for the request.

        Returns:
            bytes: The Base64 encoded PDF file content.
            None: If download fails.
        """
        pdf_file = os.path.join(self.screenshot_folder, f"{uuid.uuid1()}.pdf")

        try:
            # Set headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/pdf,application/x-pdf,application/octet-stream,text/html,*/*',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }

            # Use streaming to handle large files better
            with requests.get(url, allow_redirects=True, stream=True, timeout=timeout, headers=headers,
                              verify=False) as response:
                if response.status_code != 200:
                    print(f"PDF download failed with status code: {response.status_code}")
                    return None

                # Check content type headers for PDF or octet-stream
                content_type = response.headers.get('Content-Type', '').lower()
                is_likely_pdf = any(
                    pdf_indicator in content_type for pdf_indicator in ['pdf', 'octet-stream', 'application/'])

                if not is_likely_pdf:
                    # If content-type doesn't indicate PDF, check first few bytes
                    # PDF files typically start with %PDF
                    first_bytes = next(response.iter_content(256), b'')
                    if not first_bytes.startswith(b'%PDF'):
                        print(f"Downloaded content does not appear to be a PDF. Content-Type: {content_type}")
                        # Only return None if we're confident this isn't a PDF
                        if 'html' in content_type and b'<!DOCTYPE html>' in first_bytes:
                            return None

                # Use streaming write to handle large files
                with open(pdf_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Verify file content (at least basic header check)
                try:
                    with open(pdf_file, 'rb') as f:
                        header = f.read(10)
                        if not header.startswith(b'%PDF'):
                            print("Downloaded file may not be a valid PDF, but proceeding anyway")
                except Exception as e:
                    print(f"Error verifying PDF content: {e}")

                # Read binary file content
                with open(pdf_file, 'rb') as f:
                    pdf_data = f.read()
                print(f"PDF downloaded successfully ({os.path.getsize(pdf_file)} bytes)")
                return pdf_data

        except requests.exceptions.Timeout:
            print(f"PDF download timed out for URL: {url}")
            return None
        except requests.exceptions.TooManyRedirects:
            print(f"Too many redirects when downloading PDF from URL: {url}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"Connection error when downloading PDF from URL: {url}")
            return None
        except Exception as e:
            print(f"PDF download failed: {str(e)}")
            return None
        finally:
            # Always try to clean up the temp file
            if os.path.exists(pdf_file):
                try:
                    os.remove(pdf_file)
                except Exception as e:
                    print(f"Failed to remove temporary PDF file: {e}")

        return None

    def get_pdf_with_fallback(self, url, timeout=30):
        """
        Attempts to download a PDF with multiple fallback strategies.

        Args:
            url (str): The URL of the PDF file.
            timeout (int): Timeout in seconds for the request.

        Returns:
            bytes: The Base64 encoded PDF content or None on failure.
        """
        # Try primary method first
        result = self.get_pdf(url, timeout)
        if result:
            return result

        # Fallback 1: Try with session and different user agent
        pdf_file = os.path.join(self.screenshot_folder, f"{uuid.uuid1()}.pdf")
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                'Accept': 'application/pdf,*/*',
            })

            response = session.get(url, stream=True, timeout=timeout, verify=False)
            if response.status_code == 200:
                with open(pdf_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                with open(pdf_file, 'rb') as f:  # Read binary
                    bin_data = f.read()
                print(f"PDF downloaded with fallback session ({os.path.getsize(pdf_file)} bytes)")
                return bin_data
        except Exception as e:
            print(f"Fallback session download failed: {e}")
        finally:
            if os.path.exists(pdf_file):
                try:
                    os.remove(pdf_file)
                except:
                    pass

        # Fallback 2: Try with urllib
        pdf_file = os.path.join(self.screenshot_folder, f"{uuid.uuid1()}.pdf")
        try:
            import urllib.request
            opener = urllib.request.build_opener()
            opener.addheaders = [
                ('User-Agent',
                 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
                ('Accept', 'application/pdf,*/*')
            ]
            urllib.request.install_opener(opener)

            with urllib.request.urlopen(url, timeout=timeout) as response:
                with open(pdf_file, 'wb') as f:
                    f.write(response.read())

            with open(pdf_file, 'rb') as f:
                bin_data = f.read()
                print(f"PDF downloaded with urllib fallback ({os.path.getsize(pdf_file)} bytes)")
            return bin_data
        except Exception as e:
            print(f"Urllib fallback download failed: {e}")
        finally:
            if os.path.exists(pdf_file):
                try:
                    os.remove(pdf_file)
                except:
                    pass

        # All methods failed
        return None

    def save_image_robust(self, url, proxy=None, timeout=15):
        """Direct, robust download for images without Selenium."""
        error_codes = ""
        bin_data = None
        content_type = "image/jpeg"
        status_code = -1

        try:
            if url.startswith("data:image"):
                header, encoded = url.split(",", 1)
                bin_data = base64.b64decode(encoded)
                status_code = 200
                if "png" in header:
                    content_type = "image/png"
                elif "gif" in header:
                    content_type = "image/gif"
            else:
                # Add broader accept headers so CDNs don't block us as bots
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.google.com/'  # Against hotlink protection
                }
                proxies_dict = {"http": proxy, "https": proxy} if proxy else None

                # Use a Session for better redirect handling
                session = requests.Session()
                resp = session.get(url, headers=headers, proxies=proxies_dict, timeout=timeout, verify=False)
                status_code = resp.status_code

                if status_code == 200:
                    bin_data = resp.content
                    content_type = resp.headers.get('Content-Type', 'image/jpeg')
                    # Validation: check if the CDN returned an HTML block page instead of the image
                    if 'text/html' in content_type.lower():
                        error_codes = f"Expected image but received HTML page from server."
                        status_code = -1
                        bin_data = None
                else:
                    error_codes = f"HTTP Error {status_code}"
        except Exception as e:
            error_codes = f"Image Fetch Error: {str(e)}"

        file_path = None
        if bin_data and status_code == 200:
            # Uses existing method. Automatically packages image into ZIP file.
            file_path = self.upload_to_storage(html_content=None, bin_data=bin_data, content_type=content_type)
            if not file_path:
                error_codes += " | Failed to upload to storage"
                status_code = -1

        return {
            "file_path": file_path,
            "code": "image" if file_path else "error",
            "bin_data": len(bin_data) if bin_data else "error",
            "request": {"content_type": content_type, "status_code": status_code},
            "final_url": url,
            "meta": {"ip": "-1", "main": url},
            "error_codes": error_codes,
            "content_dict": {"": ""}
        }

    def bypass_cookie_banners(self, driver):
        """
        Hybrid Cookie Bypass: Uses domain-specific rules from rules.json (if applicable)
        AND global IDCAC heuristics (Shadow-DOM piercing, Nuke CSS).
        """
        current_url = driver.current_url
        domain = urlparse(current_url).hostname
        if not domain:
            domain = ""

        domain = domain.replace("www.", "")

        # 1. Search for specific rules for this domain in the rules.json
        specific_css = ""
        specific_click_selectors = []

        if hasattr(self, 'cookie_rules'):
            for rule in self.cookie_rules:
                urls = rule.get('urls', [])
                # Check if the current domain is part of the rule's URLs
                if any(domain in u for u in urls):
                    if 'css' in rule:
                        # Append a comma so it merges cleanly with our Nuke CSS
                        specific_css = rule['css'] + ", "

                    if 'sel' in rule:
                        # The 'sel' list in IDCAC contains objects like {"c": ".button-class", "ac": "click"}
                        for action in rule['sel']:
                            if 'c' in action and action.get('ac') == 'click':
                                specific_click_selectors.append(action['c'])
                    break  # Rule found, stop searching

        # Convert the Python list into a JS array string for the script
        js_specific_clicks = json.dumps(specific_click_selectors)

        # 2. Assemble the JS payload
        js_payload = f"""
            // ==========================================
            // 1. STORAGE FORGERY (Global)
            // ==========================================
            const fakeConsent = {{
                'cookieconsent_status': 'dismiss', 'sp_message_open': 'false', 'sp_consent': 'true',
                'OptanonAlertBoxClosed': new Date().toISOString(),
                'CookieConsent': '{{stamp:%27'+new Date().toISOString()+'%27%2Cnecessary%3Atrue%2Cpreferences%3Atrue%2Cstatistics%3Atrue%2Cmarketing%3Atrue%2Cmethod%3A%27implied%27%2Cver%3A1%2Cutc%3A1600000000000%2Cregion%3A%27de%27}}',
                'usercentrics': '{{"consents":[]}}'
            }};
            try {{
                for (let key in fakeConsent) {{
                    window.localStorage.setItem(key, fakeConsent[key]);
                    window.sessionStorage.setItem(key, fakeConsent[key]);
                }}
            }} catch(e) {{}}

            // ==========================================
            // 2. HYBRID CSS (Domain-specific + Global Nuke)
            // ==========================================
            const style = document.createElement('style');
            style.type = 'text/css';
            style.innerHTML = `
                /* DOMAIN-SPECIFIC RULES FROM JSON: */
                {specific_css}

                /* GLOBAL RULES: */
                [class^="cmpwelcome"], [class^="cmp-"], [id^="cmp-"], .cmpboxcontainer, .cmpboxinner,
                [id^="cmpbox"], [class^="cmpbox"], [class^="cmpwelcome"], .cmpboxinner, .cmpboxbtns,
                #cookie, .cookie, #cookies, .cookies, #gdpr, .gdpr, #gdpr-modal, .gdpr-modal, #GDPR, .GDPR,
                #consent, .consent, .elementor-popup-modal, #cookie-consent, .cookie-consent,
                #privacy, .privacy, #cookie-modal, .cookie-modal, #cnil, .cnil, #CNIL,
                #privacy-policy, .privacy-policy, [class*="ccm-modal"], [class*="ccm-widget"],
                #cookies-modal, .cookies-modal, #modal-cookie, .modal-cookie, #modal-cookies,
                .cc_container, .cookie-container, .cookies-wrapper, .cookie-box, .cookie__wrap, .consent-container,
                [id^="sp_message_container"], iframe[id^="sp_message_iframe"], [id^="sp_message_"],
                #usercentrics-root, #cookiebanner, #cookie-notice, [id^="cmpbox"], #BorlabsCookieBox,
                #onetrust-consent-sdk, #onetrust-banner-sdk, .onetrust-pc-dark-filter,
                #didomi-host, #didomi-popup, .didomi-popup-backdrop, .didomi-notice-popup,
                #tarteaucitronRoot, #tarteaucitronAlertBig, #CybotCookiebotDialog,
                [id*="cookie" i], [class*="cookie" i], 
                [id*="consent" i], [class*="consent" i], 
                [id*="gdpr" i], [class*="gdpr" i],
                [id*="cmp" i], [class*="cmp" i],
                [class*="ccm-"], [id*="ccm-"],
                .modal-backdrop, .ui-widget-overlay, .reveal-modal-bg, .cdk-overlay-container, .optin__backdrop {{ 
                    display: none !important; visibility: hidden !important; opacity: 0 !important; 
                    pointer-events: none !important; z-index: -9999 !important; height: 0 !important; width: 0 !important;
                }}
                /* Scroll Restoration */
                html, body, html.noscroll, body.modal-open, body.sp-message-open, body[style*="overflow"] {{
                    overflow: auto !important; overflow-y: auto !important; overflow-x: hidden !important;
                    position: static !important; height: auto !important; padding: 0 !important; margin: 0 !important;
                }}
            `;
            document.head.appendChild(style);

            // ==========================================
            // 3. TARGETED CLICKS & HEURISTICS
            // ==========================================
            // A) First, execute exact clicks from rules.json (Highest Priority)
            const specificSelectors = {js_specific_clicks};
            specificSelectors.forEach(sel => {{
                try {{
                    const el = document.querySelector(sel);
                    if (el) {{
                        el.click();
                        el.dispatchEvent(new MouseEvent('click', {{ view: window, bubbles: true, cancelable: true }}));
                    }}
                }} catch(e) {{}}
            }});

            // B) Fallback: Our global Shadow-DOM & Heuristics clicker
            const acceptRegex = /(akzeptieren|alles akzeptieren|alle akzeptieren|verstanden|zustimmen|ok|okay|zulassen|alle zulassen|alles zulassen|einverstanden|accept|accept all|allow|allow all|got it|agree|i agree|consent|accepter|tout accepter|j'accepte|compris|aceptar|aceptar todo|estoy de acuerdo|entendido|accetta|accetta tutto|acconsento|capito|accepteren|alles accepteren|akkoord|begrepen|akceptuj|zaakceptuj wszystko|zgadzam się|rozumiem|alles klar)/i;
            const negativeRegex = /(ablehnen|manage|settings|einstellungen|anpassen|configure|customize|reject|deny|decline|refuse|options|optionen|mehr|more|read|lesen)/i;

            function findAndClick(rootElement) {{
                if (!rootElement) return false;

                // Shadow-DOM iteration
                const allNodes = rootElement.querySelectorAll('*');
                for (let i = 0; i < allNodes.length; i++) {{
                    if (allNodes[i].shadowRoot) {{
                        if (findAndClick(allNodes[i].shadowRoot)) return true;
                    }}
                }}

                const clickables = rootElement.querySelectorAll('button, a, input[type="button"], input[type="submit"], div[role="button"], span[role="button"], div[class*="accept"], span[class*="accept"]');
                for (let el of clickables) {{
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) continue; 

                    let text = (el.innerText || el.value || el.getAttribute('aria-label') || el.title || '').trim().replace(/\\n/g, ' ');
                    if (!text || text.length > 35) continue; 

                    if (el.tagName.toLowerCase() === 'a' && el.href && !el.href.startsWith('javascript:') && !el.href.includes('#')) continue; 
                    if (negativeRegex.test(text)) continue;

                    // Match text or data-full-consent attribute
                    if (acceptRegex.test(text) || text.toLowerCase() === 'alle' || text.toLowerCase() === 'all' || el.getAttribute('data-full-consent') === 'true') {{
                        el.click();
                        el.dispatchEvent(new MouseEvent('click', {{ view: window, bubbles: true, cancelable: true }}));
                        return true;
                    }}
                }}
                return false;
            }}

            // Loop up to 4 times to catch slow-loading or async banners
            let attempts = 0;
            const searchInterval = setInterval(() => {{
                attempts++;
                if (findAndClick(document) || attempts >= 4) {{
                    clearInterval(searchInterval);
                }}
            }}, 1000);
        """
        try:
            driver.execute_script(js_payload)
            driver.sleep(2)
        except Exception as e:
            print(f"Warning: Cookie heuristics failed: {e}")

    def take_screenshot(self, driver):
        screenshot_folder = os.path.join(self.parentdir, "tmp")
        screenshot_file = os.path.join(screenshot_folder, f"{uuid.uuid1()}")
        temp_png = screenshot_file + ".png"
        temp_jpg = screenshot_file + ".jpg"

        # 1. Set desktop standard
        target_w = self.sources_cnf.get('max-width', 1280)

        driver.maximize_window()  # Maximize browser window for screenshot

        try:
            driver.execute_script("window.scrollTo(0,1)")
        except Exception:
            pass

        time.sleep(2)

        try:

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
                block_size = self.sources_cnf.get('block-size', 100)
                scroll_time_in_seconds = min(self.sources_cnf.get('scroll-time', 1), 0.5)  # Limit scroll time for safety
                scrolling = []

                # Calculate maximum time we should spend scrolling (not more than 15% of global timeout)
                max_scroll_time = self.GLOBAL_TIMEOUT * 0.15
                start_scroll_time = time.time()

                while current_height < height and current_height < self.sources_cnf.get('max-height', 2000):
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

            driver.maximize_window()  # Maximize browser window for screenshot
            required_height = driver.execute_script('return document.body.parentNode.scrollHeight')

            # Forcefully unlock the page scroll before simulation
            try:
                driver.execute_script("""
                    // List of common classes that lock the scroll
                    const lockClasses = ['modal-open', 'is-locked', 'no-scroll', 'fixed', 'sp-message-open'];

                    // Targeted elements: html and body
                    [document.documentElement, document.body].forEach(el => {
                        // 1. Remove inline styles that prevent scrolling
                        el.style.setProperty('overflow', 'auto', 'important');
                        el.style.setProperty('overflow-y', 'auto', 'important');
                        el.style.setProperty('position', 'static', 'important');
                        el.style.setProperty('height', 'auto', 'important');

                        // 2. Remove known lock-classes
                        lockClasses.forEach(cls => el.classList.remove(cls));

                        // 3. Remove any blur or pointer-event blocks
                        el.style.setProperty('pointer-events', 'auto', 'important');
                        el.style.setProperty('filter', 'none', 'important');
                    });

                    console.log('Scroll lock forcefully removed.');
                """)
                time.sleep(1)  # Short pause for the browser to recalculate the layout
            except Exception as e:
                print(f"Failed to unlock scroll: {e}")

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

            print(f"Change Viewport Size ({target_w}x900)")
            driver.set_window_size(target_w, 900)
            time.sleep(10)

            # Dynamic Altitude Measurement
            total_height = driver.execute_script('return document.body.parentNode.scrollHeight')

            # Max-Height from the config file as a safety net (set this to 10000 in the .ini file)
            max_allowed = self.sources_cnf.get('max-height', 5000)
            final_height = min(total_height, max_allowed)

            try:
                screenshot_base64 = driver.execute_cdp_cmd('Page.captureScreenshot', {
                    'format': 'png',
                    'captureBeyondViewport': True,
                    'clip': {
                        'width': target_w,
                        'height': final_height,
                        'x': 0,
                        'y': 0,
                        'scale': 1
                    }
                })

                with open(temp_png, "wb") as f:
                    f.write(base64.b64decode(screenshot_base64['data']))
            except Exception as e:
                print(f"CDP Screenshot failed, using Fallback: {e}")
                driver.set_window_size(target_w, final_height)
                driver.save_screenshot(temp_png)


        except Exception as e:
            print(f"Error in take_screenshot: {e}")
            driver.save_screenshot(temp_png)

        with Image.open(temp_png) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            output = io.BytesIO()
            img.save(output, format="JPEG", optimize=True, quality=100, subsampling=0)
            screenshot_bytes = output.getvalue()

        if self.sources_cnf.get("debug_screenshots", 0) != 0:
            with open(temp_jpg, "wb") as f:
                f.write(screenshot_bytes)
            print(f"Debug-Screenshot saved: {temp_jpg}")

        if os.path.exists(temp_png):
            try:
                os.remove(temp_png)
            except:
                pass

        return screenshot_bytes

    def _evaluate_content_quality(self, code, page_source, url, dict_request):
        """
        Evaluates the quality and completeness of scraped content.

        Args:
            code (str): The current status code of the scraping operation
            page_source (str): The HTML source of the page
            url (str): The URL that was scraped
            dict_request (dict): The request information including content type

        Returns:
            tuple: (is_valid, error_message) - Whether the content is valid and any error message
                is_valid is 1 if content was found
                is_valid is -1 if content was not found
        """
        # If we already have a known good state, keep it
        if code != "error" and code != "pdf":
            return 1, ""  # Return 1 for success

        # Empty content is definitely an error
        if not page_source or len(page_source) < 100:
            return -1, "Empty or minimal page content"

        # Check for common HTML structures that indicate useful content
        contains_body = "<body" in page_source.lower()
        contains_content_markers = any(marker in page_source.lower() for marker in
                                       ["<div", "<table", "<article", "<section", "<main", "<p>"])

        # For PDF URLs, we should be more lenient - even partial PDF data might be useful
        is_pdf_url = '.pdf' in url.lower() or '?pdf' in url.lower() or dict_request.get("content_type") == "pdf"

        if is_pdf_url:
            # For PDFs, check if we have enough data to be useful
            # PDF headers often start with "%PDF-"
            if "%PDF-" in page_source[:1000]:
                return 1, "Partial PDF content detected and may be usable"

        # If the page has a body and content markers, it's likely useful
        if contains_body and contains_content_markers:
            # Check if the content seems substantial
            content_length = len(page_source)

            # More than 5KB is usually a substantial page
            if content_length > 5000:
                return 1, "Substantial content detected"

            # Medium content with right structure might still be useful
            if content_length > 1000 and "<html" in page_source.lower() and "</html>" in page_source.lower():
                return 1, "Complete HTML structure detected with moderate content"

        # Default to reject the content
        return -1, "Content quality check failed"

    @abstractmethod
    def save_code(self, url, proxy, country_code, timeout):
        """
        Main method to save the content from a URL with a global timeout.
        Modified with improved process termination for Debian.

        Args:
            url (str): The URL to scrape.
            proxy (str, optional): Proxy to use for the request. Defaults to None.
            country_code (str, optional): Country code for locale settings. Defaults to None.
            timeout (int, optional): Custom timeout in seconds. If None, uses GLOBAL_TIMEOUT.

        Returns:
            dict: A dictionary containing the page content, screenshot, metadata, and any error codes.
        """
        pass


