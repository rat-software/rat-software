from datetime import datetime
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
import platform
import psutil
import zipfile
import io
import requests
from PIL import Image

# Define the path for configurations and extensions
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir = os.path.dirname(parentdir)



from libs.lib_helper import Helper

# Initialize the Helper instance
helper = Helper()

try:
    # Load configuration from file
    sources_cnf = helper.file_to_dict(os.path.join(parentdir, 'config/config_sources.ini'))

    # Determine whether to run in headless mode
    headless = sources_cnf.get('headless')

    # Add a timeout configuration with default of 300 seconds
    GLOBAL_TIMEOUT = sources_cnf.get('global_timeout', 300)

    API_KEY = sources_cnf.get('api-key')
    STORAGE_URL = sources_cnf.get('storage-url')+"/upload"
except Exception as e:
    print("Check your config_sources.ini file. Did you setup a storage server? Error loading configuration:", e)
    exit()

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

    def upload_to_storage(self, html_content, bin_data, content_type):
        zip_filename = f"{uuid.uuid4()}.zip"
        
        # 1. Create a ZIP file on the device
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            if html_content and isinstance(html_content, str) and html_content != "error":
                zf.writestr('source.html', html_content.encode('utf-8', 'ignore'))
            
            if bin_data and bin_data != "error":
                # KORREKTUR FÜR PDF-ERKENNUNG
                c_type = str(content_type).lower() if content_type else ""
                filename = 'source.pdf' if "pdf" in c_type else 'screenshot.jpg'
                zf.writestr(filename, bin_data)
        
        zip_buffer.seek(0)
        
        # 2. API or LOCAL
        
        # CASE A: We have configured an API URL -> Attempt upload
        if STORAGE_URL and "http" in STORAGE_URL:
            try:
                headers = {"X-API-Key": API_KEY}
                files = {"file": (zip_filename, zip_buffer, "application/zip")}
                
                print(f"Trying to upload to API: {STORAGE_URL}")
                response = requests.post(STORAGE_URL, headers=headers, files=files, timeout=30)
                
                if response.status_code == 200:
                    remote_filename = response.json().get("filename")
                    print(f"API upload successful: {remote_filename}")
                    return remote_filename
                else:
                    print(f"API upload failed: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"API Fehler: {e}")
        
        # CASE B: No API or upload failed -> Save locally
        try:
            local_storage_path = "/var/www/rat/storage/sources/" 
            os.makedirs(local_storage_path, exist_ok=True)
            
            local_filepath = os.path.join(local_storage_path, zip_filename)
            
            zip_buffer.seek(0)
            
            with open(local_filepath, "wb") as f:
                f.write(zip_buffer.read())
            
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
                # Force disconnect from DevTools vor dem Schließen
                try:
                    if hasattr(driver, 'execute_cdp_cmd'):
                        driver.execute_cdp_cmd('Network.disable', {})
                        driver.execute_cdp_cmd('Page.disable', {})
                except:
                    pass
                
                # Versuche alle Sessions zu beenden
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
                
                # NEU: Blockiere bekannte Cookie-Consent-Provider direkt auf Netzwerkebene
                driver.execute_cdp_cmd('Network.setBlockedURLs', {
                    "urls": [
                        "*cdn.cookielaw.org*",      # OneTrust
                        "*consent.cookiebot.com*",  # Cookiebot
                        "*trustarc.com*",           # TrustArc
                        "*quantcast.com*",          # Quantcast
                        "*usercentrics.eu*",        # Usercentrics
                        "*app.usercentrics.eu*",    # Usercentrics App
                        "*cmp.inmobi.com*",         # InMobi CMP
                        "*sourcepoint.com*",        # Sourcepoint
                        "*cdn.privacy-mgmt.com*",   # Privacy Manager
                        "*cookie-script.com*"       # Cookie-Script
                    ]
                })
                print("CDP: Cookie consent provider successfully blocked.")
            except Exception as e:
                print(f"CDP Network enable/block failed: {e}")

            # Sammeln der Netzwerkantworten
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
            print("Versuche normale get_url_header")
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
            socket.setdefaulttimeout(30)  # 10 seconds timeout
            
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
            print(f"Fehler bei der Verbindung: {e}")
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
                print(f"Fehler bei der Verbindung: {e}")
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
            with requests.get(url, allow_redirects=True, stream=True, timeout=timeout, headers=headers, verify=False) as response:
                if response.status_code != 200:
                    print(f"PDF download failed with status code: {response.status_code}")
                    return None
                    
                # Check content type headers for PDF or octet-stream
                content_type = response.headers.get('Content-Type', '').lower()
                is_likely_pdf = any(pdf_indicator in content_type for pdf_indicator in ['pdf', 'octet-stream', 'application/'])
                
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
                
                # Encode the file content
                with open(pdf_file, 'rb') as f:
                    pdf_data = f.read() # Rohe Bytes
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


    # Fallback method for cases where direct download fails
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
                
                with open(pdf_file, 'rb') as f: # Binär einlesen
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
                ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
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



    def take_screenshot(self, driver):
        """
        Optimierte Screenshot-Funktion basierend auf dem erfolgreichen Standalone-Test.
        """
        screenshot_folder = os.path.join(parentdir, "tmp")
        screenshot_file = os.path.join(screenshot_folder, f"{uuid.uuid1()}")
        temp_png = screenshot_file + ".png"
        temp_jpg = screenshot_file + ".jpg"

        # 1. Desktop-Standard setzen
        target_w = sources_cnf.get('max-width', 1280)

        driver.maximize_window()  # Maximize browser window for screenshot

        try:
            driver.execute_script("window.scrollTo(0,1)")
        except Exception:
            pass

        time.sleep(2)

        try:
           
            try:
                driver.execute_script("""
                    // 1. Storage Forgery (Prevents multiple banners from spawning)
                    const fakeConsentData = {
                        'cookieconsent_status': 'dismiss',
                        'sp_message_open': 'false', 
                        'sp_consent': 'true',
                        'OptanonAlertBoxClosed': new Date().toISOString()
                    };
                    for (const [key, value] of Object.entries(fakeConsentData)) {
                        try { window.localStorage.setItem(key, value); } catch(e) {}
                        try { window.sessionStorage.setItem(key, value); } catch(e) {}
                    }

                    // 2. THE RULES.JS CSS INJECTION (Hides banners and forces scrolling)
                    const style = document.createElement('style');
                    style.type = 'text/css';
                    style.innerHTML = `
                        /* Aus der commons Liste extrahierte und gebündelte Selektoren */
                        #cookie, .cookie, #cookies, .cookies, #gdpr, .gdpr, #gdpr-modal, .gdpr-modal, #GDPR, .GDPR,
                        #consent, .consent, .elementor-popup-modal, #cookie-consent, .cookie-consent,
                        #privacy, .privacy, #cookie-modal, .cookie-modal, #cnil, .cnil, #CNIL,
                        #privacy-policy, .privacy-policy, #privacyPolicy, .privacyPolicy,
                        #cookies-modal, .cookies-modal, #modal-cookie, .modal-cookie, #modal-cookies, .modal-cookies,
                        .cc_container, .cookie-container, .cookies-wrapper, .cookie-box, .cookie__wrap, .consent-container,
                        [id^="sp_message_container"], iframe[id^="sp_message_iframe"], [id^="sp_message_"],
                        #usercentrics-root, #cookiebanner, #cookie-notice, [id^="cmpbox"], #BorlabsCookieBox,
                        #onetrust-consent-sdk, #onetrust-banner-sdk, .onetrust-pc-dark-filter,
                        #didomi-host, #didomi-popup, .didomi-popup-backdrop, .didomi-notice-popup,
                        #tarteaucitronRoot, #tarteaucitronAlertBig,
                        /* Overlays and backdrops that block clicks */
                        .modal-backdrop, .ui-widget-overlay, .reveal-modal-bg, .cdk-overlay-container, .optin__backdrop
                        { 
                            display: none !important; 
                            visibility: hidden !important; 
                            opacity: 0 !important; 
                            pointer-events: none !important; 
                            width: 0 !important; 
                            height: 0 !important; 
                            z-index: -9999 !important;
                        }

                        /* Key points from Commons Rules 2, 14, and 85: Scrolling must be restored! */
                        html, body, html.noscroll, body.modal-open, body.sp-message-open, body[style*="overflow"] {
                            overflow: auto !important;
                            overflow-y: auto !important;
                            position: static !important;
                            height: auto !important;
                            padding-right: 0px !important;
                        }
                    `;
                    document.head.appendChild(style);

                    // 3. IDCAC CLICKER (In case making an element invisible on a page breaks the layout)
                    const acceptRegex = /(akzeptieren|alles akzeptieren|alle akzeptieren|verstanden|zustimmen|ok|okay|zulassen|alle zulassen|alles zulassen|einverstanden|accept|accept all|allow|allow all|got it|agree|i agree|consent|accepter|tout accepter|j'accepte|compris|aceptar|aceptar todo|estoy de acuerdo|entendido|accetta|accetta tutto|acconsento|capito|accepteren|alles accepteren|akkoord|begrepen|akceptuj|zaakceptuj wszystko|zgadzam się|rozumiem)/i;
                    const negativeRegex = /(ablehnen|manage|settings|einstellungen|anpassen|configure|customize|reject|deny|decline|refuse|options|optionen|mehr|more|read|lesen)/i;
                    
                    const elements = document.querySelectorAll('button, a, input[type="button"], input[type="submit"], div[role="button"], span[role="button"]');
                    
                    for (let el of elements) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) continue;
                        
                        let text = (el.innerText || el.value || el.getAttribute('aria-label') || el.title || '').trim().replace(/\\n/g, ' ');
                        if (!text || text.length > 35) continue; // 
                        
                        if (el.tagName.toLowerCase() === 'a' && el.href && !el.href.startsWith('javascript:') && !el.href.includes('#')) continue; 
                        if (negativeRegex.test(text)) continue;

                        if (acceptRegex.test(text) || text.toLowerCase() === 'alle' || text.toLowerCase() === 'all') {
                            const mouseEvent = new MouseEvent('click', { view: window, bubbles: true, cancelable: true });
                            el.dispatchEvent(mouseEvent);
                            break;
                        }
                    }
                """)
                time.sleep(3)
            except Exception as e:
                print(f"Errors in cookie heuristics: {e}")

            time.sleep(3)

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
                time.sleep(1) # Short pause for the browser to recalculate the layout
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
            max_allowed = sources_cnf.get('max-height', 5000)
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
                print(f"CDP Screenshot fehlgeschlagen, nutze Fallback: {e}")
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

        if sources_cnf.get("debug_screenshots", 0) != 0:
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


    

    def save_code(self, url, proxy=None, country_code=None, timeout=None):
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
        # Required imports for process termination
        import subprocess
        import platform
        import signal
        import os
        import time
        import psutil
        import threading
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
        
        # Use custom timeout if provided, otherwise use GLOBAL_TIMEOUT
        actual_timeout = timeout if timeout is not None else GLOBAL_TIMEOUT
        
        # Track the start time immediately
        start_time = time.time()
        
        # Safety check for URL format
        if not url.startswith(('http://', 'https://')):
            return {
                "code": "error", 
                "bin_data": "error", 
                "request": {"content_type": "error", "status_code": -1}, 
                "final_url": url, 
                "meta": {"ip": "-1", "main": url}, 
                "error_codes": "Invalid URL format", 
                "content_dict": {"":""},
                "execution_time": 0
            }
        
        # Define a killer function using direct system commands
        def killer(proc_id):
            try:
                if platform.system() != 'Windows':
                    # Unix-based systems - use direct kill commands
                    try:
                        print(f"Attempting to terminate process {proc_id} with SIGTERM")
                        # First try SIGTERM (15) - graceful termination
                        subprocess.run(f"kill -15 {proc_id}", shell=True)
                        
                        # Give it a moment to terminate
                        time.sleep(0.5)
                        
                        # Check if process still exists and use SIGKILL if needed
                        try:
                            os.kill(proc_id, 0)  # Signal 0 is used to check if process exists
                            print(f"Process {proc_id} still running, using SIGKILL")
                            subprocess.run(f"kill -9 {proc_id}", shell=True)
                        except OSError:
                            # Process no longer exists
                            print(f"Process {proc_id} terminated successfully with SIGTERM")
                    
                        # Also kill any child processes
                        print("Attempting to kill any child processes")
                        subprocess.run(f"pkill -9 -P {proc_id}", shell=True)
                        
                        # Additional cleanup for chrome and chromedriver processes
                        print("Cleaning up any remaining browser processes")
                        subprocess.run("pkill -9 -f chrome", shell=True)
                        subprocess.run("pkill -9 -f chromedriver", shell=True)
                    except Exception as e:
                        print(f"Error in Unix process termination: {e}")
                else:
                    # Windows - use existing psutil approach
                    try:
                        parent = psutil.Process(proc_id)
                        children = parent.children(recursive=True)
                        for child in children:
                            child.kill()
                        parent.kill()
                    except psutil.NoSuchProcess:
                        pass
                    except Exception as e:
                        print(f"Error in Windows process termination: {e}")
            except Exception as e:
                print(f"Failed to kill process {proc_id}: {e}")
        
        # Use ThreadPoolExecutor with timeout for the entire function
        with ThreadPoolExecutor(max_workers=1) as executor:
            # Create a managed thread for execution
            future = executor.submit(self._save_code_worker, url, proxy, country_code, start_time, actual_timeout)
            
            # Get the thread's ID - useful in case we need to manage it
            worker_thread = None
            for thread in threading.enumerate():
                if thread.name.startswith('ThreadPoolExecutor'):
                    worker_thread = thread
                    break
                    
            try:
                # The key is to firmly enforce the timeout here with future.result()
                result = future.result(timeout=actual_timeout + 5)  # Add 5 seconds grace period for cleanup
                # Add execution time to the result
                result["execution_time"] = time.time() - start_time
                return result
            except FutureTimeoutError:
                # Handle timeout exception
                elapsed_time = time.time() - start_time
                print(f"Scraping timed out after {elapsed_time:.2f} seconds for URL: {url}")
                
                # Try to forcefully cancel the future
                cancelled = future.cancel()
                print(f"Future cancelled: {cancelled}")
                
                # In case of timeout, use improved process termination
                try:
                    current_process = psutil.Process()
                    parent_pid = current_process.pid
                    print(f"Finding and terminating child processes of {parent_pid}")
                    
                    # DEBIAN SPECIFIC: Use system commands for more reliable process termination
                    # 1. First try to use psutil to find browser processes
                    found_processes = []
                    try:
                        # Find and terminate all child processes
                        children = current_process.children(recursive=True)
                        for child in children:
                            try:
                                # Skip vital system processes
                                if child.name().lower() in ('python', 'python.exe'):
                                    continue
                                    
                                # Skip any non-chrome, non-driver processes
                                if not any(x in child.name().lower() for x in ('chrome', 'driver', 'selenium')):
                                    continue
                                    
                                print(f"Terminating child process: {child.pid} ({child.name()})")
                                found_processes.append(child.pid)
                                subprocess.run(f"kill -9 {child.pid}", shell=True)
                            except Exception as e:
                                print(f"Error killing process {child.pid}: {e}")
                    except Exception as e:
                        print(f"Error finding child processes: {e}")
                    
                    # 2. If no processes found with psutil, or as an additional measure,
                    # use direct system commands to find and kill browser processes
                    if not found_processes:
                        print("Using system commands to find and terminate browser processes")
                        try:
                            # Find chrome processes
                            ps_chrome = subprocess.run("ps aux | grep -i chrome | grep -v grep | awk '{print $2}'", 
                                                    shell=True, capture_output=True, text=True)
                            chrome_pids = ps_chrome.stdout.strip().split('\n')
                            
                            # Find chromedriver processes
                            ps_driver = subprocess.run("ps aux | grep -i chromedriver | grep -v grep | awk '{print $2}'", 
                                                    shell=True, capture_output=True, text=True)
                            driver_pids = ps_driver.stdout.strip().split('\n')
                            
                            # Kill found processes
                            for pid in chrome_pids + driver_pids:
                                if pid and pid.strip():
                                    print(f"Killing process {pid} found via ps")
                                    subprocess.run(f"kill -9 {pid}", shell=True)
                        except Exception as e:
                            print(f"Error using system commands to kill processes: {e}")
                    
                    # 3. Final broad attempt with pkill (will catch anything we missed)
                    try:
                        print("Final cleanup with pkill")
                        subprocess.run("pkill -9 -f chrome", shell=True)
                        subprocess.run("pkill -9 -f chromedriver", shell=True)
                        subprocess.run("pkill -9 -f selenium", shell=True)
                    except Exception as e:
                        print(f"Error with pkill cleanup: {e}")
                        
                except Exception as e:
                    print(f"Error during forced process termination: {str(e)}")
                
                # Return error information with the SAME STRUCTURE as the original
                return {
                    "code": "error", 
                    "bin_data": "error", 
                    "request": {"content_type": "error", "status_code": -1}, 
                    "final_url": url, 
                    "meta": {"ip": "-1", "main": url}, 
                    "error_codes": f"Execution timed out after {elapsed_time:.2f} seconds (limit: {actual_timeout}s). Forced termination applied.", 
                    "content_dict": {"":""},
                    "execution_time": elapsed_time
                }
            except Exception as e:
                # Handle any other exceptions that might occur
                elapsed_time = time.time() - start_time
                print(f"Error during scraping: {str(e)}")
                return {
                    "code": "error", 
                    "bin_data": "error", 
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
            proxy (str, optional): Proxy to use for the request.
            country_code (str, optional): Country code for locale settings.
            start_time (float, optional): Time when the operation started. Used for timeout checks.
            timeout (int, optional): Timeout in seconds.
                    
        Returns:
            dict: A dictionary containing the page content, screenshot, metadata, and any error codes.
        """
        # Create a cancellation event
        cancel_event = threading.Event()
        driver_instance = {"driver": None}  # Using dict to allow modification in nested functions
        
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

        # 1. DIRECT PDF PRE-CHECK (Bypasses the browser entirely!)
        is_likely_pdf = False
        parsed_path = urlparse(url).path.lower()
        if parsed_path.endswith('.pdf') or '?pdf' in url.lower() or '&pdf' in url.lower():
            is_likely_pdf = True
        else:
            try:
                proxies_dict = {"http": proxy, "https": proxy} if proxy else None
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                head_resp = requests.head(url, timeout=5, verify=False, allow_redirects=True, proxies=proxies_dict, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                if 'pdf' in head_resp.headers.get('Content-Type', '').lower():
                    is_likely_pdf = True
            except:
                pass
                
        if is_likely_pdf:
            print(f"PDF erkannt VOR Browser-Start: {url}")
            pdf_data = self.get_pdf_with_fallback(url, timeout=30)
            if pdf_data:
                print("PDF erfolgreich direkt heruntergeladen, überspringe Browser!")
                try:
                    meta = self.get_result_meta(url)
                except: 
                    pass
                file_path = self.upload_to_storage("pdf", pdf_data, "application/pdf")
                return {
                    "file_path": file_path,
                    "code": None, 
                    "bin_data": None,
                    "request": {"content_type": "application/pdf", "status_code": 200},
                    "final_url": url,
                    "meta": meta,
                    "error_codes": "",
                    "content_dict": {"":""}
                }
            else:
                print("Direct PDF download failed; starting normal browser process...")
        # =========================================================================

        # Watchdog timer that can forcefully terminate operations if needed
        def watchdog_timer():
            watchdog_sleep = min(timeout * 0.1, 30)  # Check every 10% of timeout or 30 seconds, whichever is less
            while not cancel_event.is_set():
                elapsed = time.time() - start_time
                if elapsed > timeout * 0.95:  # 95% of timeout used
                    print(f"Watchdog timeout triggered after {elapsed:.2f}s for {url}")
                    # Force cleanup if driver exists
                    try:
                        if driver_instance["driver"]:
                            print("Watchdog forcing driver cleanup")
                            self._cleanup_driver(driver_instance["driver"])
                            driver_instance["driver"] = None
                    except Exception as e:
                        print(f"Watchdog cleanup error: {e}")
                    
                    # Force termination of any stuck child processes
                    try:
                        current_process = psutil.Process()
                        children = current_process.children(recursive=True)
                        for child in children:
                            try:
                                print(f"Terminating child process: {child.pid}")
                                child.terminate()
                                time.sleep(0.5)
                                if child.is_running():
                                    print(f"Force killing child process: {child.pid}")
                                    child.kill()
                            except Exception as e:
                                print(f"Error killing process {child.pid}: {e}")
                    except Exception as e:
                        print(f"Error handling child processes: {e}")

                    try:
                        if platform.system() != 'Windows':
                            print("Killing any remaining Chrome processes")
                            os.system("pkill -f 'chrome' || true")
                            os.system("pkill -f 'chromedriver' || true")
                    except Exception as e:
                        print(f"Error killing Chrome processes: {e}")                        
                        
                    # Set the cancellation event
                    cancel_event.set()
                    return
                
                if cancel_event.wait(watchdog_sleep):
                    return
        
        # Start watchdog in a separate thread
        watchdog_thread = threading.Thread(target=watchdog_timer, daemon=True)
        watchdog_thread.start()
        
        try:
            # Add inner timeout checker that can be used throughout the function
            def check_remaining_time():
                """Check if we're out of time and should abort processing"""
                elapsed = time.time() - start_time
                if elapsed > timeout * 0.95:  # 95% of timeout used
                    cancel_event.set()  # Signal the watchdog to stop
                    return True
                return False
            
            # Function to check if we're approaching timeout
            def check_timeout(percentage, operation_name=""):
                if cancel_event.is_set():
                    return True
                    
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
                return {"code": "error", "bin_data": "error", "request": dict_request, "final_url": url, 
                    "meta": meta, "error_codes": error_codes, "content_dict": content_dict}
            
            # Configure Driver with appropriate settings
            driver_options = {
                "browser": "chrome",
                "wire": False,
                "uc": True,
                "headless2": headless,
                "incognito": False,
                "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "do_not_track": True,
                "undetectable": True,
                "no_sandbox": True
            }
                       
            if proxy:
                driver_options["proxy"] = proxy

            if country_code:
                driver_options["locale_code"] = country_code
                
            # Check if we've already used too much time before even starting the driver
            if check_timeout(0.1, "pre-driver initialization") or cancel_event.is_set():
                return {"code": "error", "bin_data": "error", "request": dict_request, "final_url": url, 
                    "meta": meta, "error_codes": error_codes, "content_dict": content_dict}
                        
            # Driver initialization with timeout
            try:
                # Create the driver with a timeout for its creation
                MAX_DRIVER_INIT_TIME = min(60, timeout * 0.2)  # 20% of total timeout or 60s max
                driver_init_start = time.time()
                
                # Set a timeout for driver initialization
                def init_driver():
                    if cancel_event.is_set():
                        return None
                    return Driver(**driver_options)
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future_driver = executor.submit(init_driver)
                    try:
                        driver = future_driver.result(timeout=MAX_DRIVER_INIT_TIME)
                        driver_instance["driver"] = driver  # Store in the shared dict for watchdog access
                    except Exception as e:
                        error_codes += f"Driver initialization timeout after {time.time() - driver_init_start:.2f}s: {str(e)}; "
                        return {"code": "error", "bin_data": "error", "request": dict_request, "final_url": url, 
                            "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

                # Check if we're out of time after driver init or if cancellation was requested
                if check_remaining_time() or cancel_event.is_set():
                    error_codes += "Timeout after driver initialization; "
                    self._cleanup_driver(driver)
                    driver_instance["driver"] = None
                    return {"code": "error", "bin_data": "error", "request": dict_request, "final_url": url, 
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
                return {"code": "error", "bin_data": "error", "request": dict_request, "final_url": url, 
                    "meta": meta, "error_codes": error_codes, "content_dict": content_dict}
            
            # Check timeout after driver initialization
            if check_timeout(0.3, "driver initialization") or cancel_event.is_set():
                if driver:
                    self._cleanup_driver(driver)
                    driver_instance["driver"] = None
                return {"code": "error", "bin_data": "error", "request": dict_request, "final_url": url, 
                    "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

            # Set up the page load with its own timeout
            page_load_success = False
            try:
                # Use a more defensive page loading approach with a separate thread
                def load_page():
                    if cancel_event.is_set():
                        return False
                        
                    nonlocal driver
                    try:
                        driver.get(url)
                        return True
                    except TimeoutException:
                        # If we hit a timeout during page load, check if we got useful content
                        try:
                            content_length = len(driver.page_source) if driver.page_source else 0
                            if content_length > 500:  # If we have substantial content
                                print(f"Page load timed out but received {content_length} bytes of content. Processing anyway.")
                                return "partial"  # Return a special value to indicate partial success
                            return False
                        except:
                            return False
                    except Exception:
                        return False
                
                with ThreadPoolExecutor(max_workers=1) as page_executor:
                    page_future = page_executor.submit(load_page)

                    try:
                        page_load_success = page_future.result(timeout=page_load_timeout)
                        # If we got "partial" success, convert it to a boolean but track it separately
                        if page_load_success == "partial":
                            error_codes += "Page load timed out but substantial content was retrieved; proceeding with partial content; "
                            page_load_success = True
                    except Exception as e:
                        error_codes += f"Page load timeout: {str(e)}; "
                        # Check if we have useful content despite the timeout
                        try:
                            content_length = len(driver.page_source) if driver.page_source else 0
                            if content_length > 500:  # If we have substantial content
                                print(f"Page load timed out but received {content_length} bytes of content. Processing anyway.")
                                page_load_success = True
                                error_codes += "Processing with partial content; "
                                
                                # Evaluate if this partial content is valuable while preserving status codes
                                try:
                                    # First, get the actual HTTP status code if possible
                                    try:
                                        responses = driver.execute_script("return window.performance.getEntries().map(e => { return {url: e.name, status: e.responseStatus}; });")
                                        for resp in responses:
                                            if url in resp.get('url', ''):
                                                actual_status = resp.get('status')
                                                if actual_status and actual_status > 0:
                                                    dict_request["status_code"] = actual_status
                                                    break
                                    except Exception:
                                        # If we can't get status from performance entries, default to -1
                                        if dict_request["status_code"] <= 0:
                                            dict_request["status_code"] = -1
                                    
                                    # Evaluate content quality
                                    is_valid, quality_message = self._evaluate_content_quality("error", driver.page_source, url, dict_request)
                                    
                                    # Get original status code
                                    original_status = dict_request.get('status_code', -1)
                                    
                                    if is_valid == 1:  # Content is good quality
                                        dict_request["content_type"] = "html"  # Set content type for proper handling
                                        
                                        # Handle status codes appropriately
                                        if original_status in [403, 404, 500, 502, 503]:
                                            # For important error codes, preserve them but mark content as found
                                            dict_request["content_found"] = True
                                            error_codes += f"Good quality content found despite status code {original_status} and timeout: {quality_message}; "
                                        elif original_status < 0 or original_status == 0:
                                            # No valid status code was found - this is a pure timeout with content
                                            # Set to 200 to allow progress=1 since we have good content
                                            dict_request["status_code"] = 200
                                            dict_request["recovered"] = True
                                            error_codes += f"Unknown status code but good content found despite timeout: {quality_message}; "
                                        elif original_status == 200:
                                            # Status was already 200, just record the quality finding
                                            error_codes += f"Status code 200 with good content despite timeout: {quality_message}; "
                                        else:
                                            # For non-critical status codes, we preserve them but mark content as found
                                            dict_request["content_found"] = True
                                            error_codes += f"Good quality content found despite status code {original_status} and timeout: {quality_message}; "
                                except Exception as ev:
                                    error_codes += f"Error evaluating partial content: {str(ev)}; "
                            else:
                                page_load_success = False
                        except:
                            page_load_success = False
                
                # Calculate safe wait time based on remaining time
                safe_wait_time = min(sources_cnf.get('wait_time', 3), timeout * 0.05)
                
                # Only wait if we have enough time and page loading was at least attempted
                if page_load_success and not check_timeout(0.5, "page loading") and not cancel_event.is_set():
                    time.sleep(safe_wait_time)
            except Exception as e:
                error_codes += f"URL unreachable: {e}; "
                if driver:
                    self._cleanup_driver(driver)
                    driver_instance["driver"] = None
                return {"code": "error", "bin_data": "error", "request": dict_request, "final_url": url, 
                    "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

            # Forced timeout check - if we're approaching timeout, return what we have
            if check_remaining_time() or cancel_event.is_set():
                error_codes += "Timeout after page load; "
                if driver:
                    try:
                        # Try to get at least something before cleanup
                        try:
                            code = driver.page_source
                            if code and len(code) > 500:
                                # We have substantial content, encode it
                                is_valid, message = self._evaluate_content_quality(code, code, url, dict_request)
                                if is_valid:
                                    # Try to take a screenshot if we don't already have one
                                    try:
                                        if not bin_data:
                                            # Use a very short timeout since we're already at the timeout boundary
                                            timeout_screenshot = min(10, (timeout - (time.time() - start_time)) * 0.8)
                                            if timeout_screenshot > 3:  # Only attempt if we have at least 3 seconds
                                                def quick_screenshot():
                                                    return self.take_screenshot(driver)
                                                
                                                with ThreadPoolExecutor(max_workers=1) as ss_exec:
                                                    ss_future = ss_exec.submit(quick_screenshot)
                                                    bin_data = ss_future.result(timeout=timeout_screenshot)
                                    except Exception as e:
                                        error_codes += f"Emergency screenshot failed: {str(e)}; "
                                    
                                    code = code
                                    dict_request["content_type"] = "html"
                                    # Critical for ensuring progress=1
                                    dict_request["status_code"] = 200
                                    dict_request["recovered"] = True
                                    error_codes += f"Partial content saved: {message}; "
                        except Exception as e:
                            error_codes += f"Content recovery during timeout failed: {str(e)}; "
                        
                        self._cleanup_driver(driver)
                        driver_instance["driver"] = None
                    except:
                        pass
                result_dict = {
                    "code": code if code and code != "error" else "error",
                    "bin_data": bin_data,
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
                if check_timeout(0.6, "before header retrieval") or cancel_event.is_set():
                    dict_request = {"content_type": "error", "status_code": -1}
                else:
                    # Use CDP-based header detection with its own timeout
                    header_start = time.time()
                    MAX_HEADER_TIME = min(60, timeout * 0.30)  # 15% of total or 20s max
                    
                    def get_headers():
                        if cancel_event.is_set():
                            return {"content_type": "error", "status_code": -1}
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
            if check_remaining_time() or cancel_event.is_set():
                error_codes += "Timeout after header retrieval; "
                if driver:
                    self._cleanup_driver(driver)
                    driver_instance["driver"] = None
                return {"code": "error", "bin_data": "error", "request": dict_request, "final_url": url, 
                    "meta": meta, "error_codes": error_codes, "content_dict": content_dict}

            # Main content processing
            try:
                if dict_request["status_code"] == 200 and not cancel_event.is_set():
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
                    if check_remaining_time() or cancel_event.is_set():
                        error_codes += "Timeout before content processing; "
                        if driver:
                            self._cleanup_driver(driver)
                            driver_instance["driver"] = None
                        return {"code": code if code and code != "error" else "error", 
                                "bin_data": bin_data,
                                "request": dict_request, 
                                "final_url": final_url, 
                                "meta": meta, 
                                "error_codes": error_codes, 
                                "content_dict": content_dict}

                    if code != "error" and not cancel_event.is_set():
                        # Check timeout before heavy operations
                        if check_timeout(0.7, "before processing content") or cancel_event.is_set():
                            code = "error"
                        elif "pdf" in dict_request["content_type"]:
                            try:
                                # Use a timeout for PDF download
                                MAX_PDF_TIME = min(30, timeout * 0.2)
                                pdf_start = time.time()
                                
                                def get_pdf_data():
                                    if cancel_event.is_set():
                                        return None
                                    return self.get_pdf_with_fallback(url, timeout=MAX_PDF_TIME)
                                
                                with ThreadPoolExecutor(max_workers=1) as pdf_executor:
                                    pdf_future = pdf_executor.submit(get_pdf_data)
                                    try:
                                        bin_data = pdf_future.result(timeout=MAX_PDF_TIME)
                                        if bin_data:
                                            code = "pdf"
                                        else:
                                            # Even if the direct PDF download failed, we might have 
                                            # useful content in the driver already
                                            page_source = driver.page_source
                                            if page_source and len(page_source) > 1000:
                                                # Check if this might be PDF content that was rendered in the browser
                                                if "pdf" in page_source.lower()[:1000] or "adobe" in page_source.lower()[:1000]:
                                                    print("PDF download failed but PDF might be embedded in page. Processing as HTML.")
                                                    code = page_source
                                                    dict_request["content_type"] = "html"
                                                    error_codes += "PDF download failed but processing embedded PDF as HTML; "
                                                else:
                                                    code = "error"
                                                    error_codes += "PDF download returned empty data; "
                                            else:
                                                code = "error"
                                                error_codes += "PDF download returned empty data; "
                                    except Exception as e:
                                        error_codes += f"PDF download timeout after {time.time() - pdf_start:.2f}s: {str(e)}; "
                                        
                                        # Try alternative approach - some PDFs can be viewed in the browser directly
                                        try:
                                            page_source = driver.page_source
                                            if page_source and len(page_source) > 1000:
                                                code = page_source
                                                dict_request["content_type"] = "html"
                                                error_codes += "Using browser-rendered PDF content as fallback; "
                                            else:
                                                code = "error"
                                        except:
                                            code = "error"
                                        
                            except Exception as e:
                                code = "error"
                                error_codes += f"PDF download failed: {e}; "
                        else:
                            try:
                                # Calculate safe wait time based on remaining time
                                remaining_time = timeout - (time.time() - start_time)
                                safe_wait_time = min(sources_cnf.get('wait_time', 3), remaining_time * 0.05)
                                
                                if remaining_time > 10 and not cancel_event.is_set():  # Only wait if we have enough time
                                    time.sleep(safe_wait_time)
                                
                                # Only take screenshot if we have enough time
                                if check_timeout(0.8, "before screenshot") or cancel_event.is_set():
                                    code = "error"
                                else:
                                    # Use a timeout for screenshot
                                    MAX_SCREENSHOT_TIME = min(60, timeout * 0.15)
                                    screenshot_start = time.time()
                                    
                                    def take_screenshot_with_timeout():
                                        if cancel_event.is_set():
                                            return None
                                        return self.take_screenshot(driver)
                                    
                                    with ThreadPoolExecutor(max_workers=1) as screenshot_executor:
                                        screenshot_future = screenshot_executor.submit(take_screenshot_with_timeout)
                                        try:
                                            bin_data = screenshot_future.result(timeout=MAX_SCREENSHOT_TIME)
                                            if bin_data:
                                                code = code
                                                dict_request["content_type"] = "html"
                                            else:
                                                error_codes += "Screenshot returned empty data; "
                                                # Still try to encode the code even if screenshot fails
                                                try:
                                                    code = code
                                                    dict_request["content_type"] = "html"
                                                except:
                                                    code = "error"
                                        except Exception as e:
                                            error_codes += f"Screenshot timeout after {time.time() - screenshot_start:.2f}s: {str(e)}; "
                                            # Still try to encode the code even if screenshot fails
                                            try:
                                                code = code
                                                dict_request["content_type"] = "html"
                                            except:
                                                code = "error"
                                                bin_data = "error"
                                    
                            except Exception as e:
                                code = "error"
                                error_codes += f"Screenshot / HTML failed: {e}; "
                    else:
                        code = "error"
                        error_codes += f"Invalid page content; "
                else:
                    # Even with wrong status code, check if we have valuable content
                    try:
                        page_source = driver.page_source
                        is_valid, message = self._evaluate_content_quality(code, page_source, url, dict_request)
                        
                        # Store the original status code - never modify it unless it's explicitly 200
                        original_status = dict_request.get('status_code', -1)
                        
                        if is_valid == 1:  # Content quality is good
                            # Take a screenshot here before encoding the content
                            try:
                                if not bin_data:  # Only if we don't already have a screenshot
                                    screenshot_start = time.time()
                                    MAX_SCREENSHOT_TIME = min(20, timeout * 0.15)
                                    
                                    def take_screenshot_with_timeout():
                                        if cancel_event.is_set():
                                            return None
                                        return self.take_screenshot(driver)
                                    
                                    with ThreadPoolExecutor(max_workers=1) as screenshot_executor:
                                        screenshot_future = screenshot_executor.submit(take_screenshot_with_timeout)
                                        bin_data = screenshot_future.result(timeout=MAX_SCREENSHOT_TIME)
                                        if not bin_data:
                                            error_codes += "Failed to take screenshot for recovered content; "
                            except Exception as e:
                                error_codes += f"Screenshot attempt for recovered content failed: {str(e)}; "
                            
                            # Now encode the content
                            code = page_source
                            dict_request["content_type"] = "html"
                            
                            # Only preserve status_code=200 if that's what the server actually returned
                            # For all other codes, add a flag but don't modify the status code
                            if original_status == 200:
                                # Status code is already 200, no need to change
                                error_codes += f"{message}; "
                            else:
                                # For error status codes, add content_found flag but KEEP the original status
                                dict_request["content_found"] = True
                                error_codes += f"Content found despite status code {original_status}: {message}; "
                                # Do NOT set status_code to 200 here
                        else:
                            code = "error"
                            error_codes += f"Status code {dict_request['status_code']} with insufficient content: {message}; "
                    except Exception as e:
                        code = "error"
                        error_codes += f"Content evaluation failed: {str(e)}; "


            except Exception as e:
                error_codes += f"Content processing failed: {e}; "
                code = "error"
            finally:
                # Always clean up the driver at the end of processing
                if driver:
                    self._cleanup_driver(driver)
                    driver_instance["driver"] = None

        except Exception as e:
            error_codes += f"Content processing failed: {e}; "
            code = "error"
        finally:
            # Always clean up the driver at the end of processing
            if driver_instance["driver"]:
                self._cleanup_driver(driver_instance["driver"])
                driver_instance["driver"] = None
            
            # Signal watchdog to stop
            cancel_event.set()
            
            # Wait for watchdog thread to finish (with timeout)
            watchdog_thread.join(2.0)

        # Final check if we've exceeded our time limit
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            error_codes += f"Process exceeded the timeout limit of {timeout} seconds (took {elapsed_time:.2f}s); "
            code = "error"

        print(f"DEBUG: Status of 'code': {'content found' if code and code != 'error' else 'empty or error'}")
        print(f"DEBUG: Length of 'bin_data': {len(bin_data) if bin_data and bin_data != 'error' else 0} Bytes")
        print(f"DEBUG: Content-Type: {dict_request.get('content_type')}")

        file_path = self.upload_to_storage(code, bin_data, dict_request.get("content_type"))

        result_dict = {
            "file_path": file_path,
            "code": len(code), 
            "bin_data": len(bin_data),
            "request": dict_request,
            "final_url": final_url,
            "meta": meta,
            "error_codes": error_codes,
            "content_dict": content_dict
        }
        return result_dict