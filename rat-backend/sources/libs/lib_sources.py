from lib_scraper import LibScraper
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from seleniumbase import Driver
import uuid
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import socket
import base64
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
import json




class Sources(LibScraper):
    """
    A class to handle web scraping tasks, including saving webpage content,
    taking screenshots, and handling PDF files.
    """

    # Fallback method for cases where direct download fails

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
        import os
        import time
        import psutil
        import threading
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
        
        # Use custom timeout if provided, otherwise use GLOBAL_TIMEOUT
        actual_timeout = timeout if timeout is not None else self.GLOBAL_TIMEOUT
        
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
        
    def _save_code_worker(self, url, proxy=None, country_code=None, start_time=None, timeout=None):
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
        # fallback for time-out
        if timeout is None:
            timeout = self.GLOBAL_TIMEOUT

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
            print(f"PDF detected BEFORE starting browser: {url}")
            pdf_data = self.get_pdf_with_fallback(url, timeout=30)
            if pdf_data:
                print("PDF successfully downloaded directly, skipping browser!")
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
                "headless2": self.headless,
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
                        error_name = type(e).__name__
                        error_msg = str(e) if str(e) else "Time limit exceeded."
                        error_codes += f"Driver initialization timeout after {time.time() - driver_init_start:.2f}s: [{error_name}] {error_msg}; "
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
                    
                    # --- NEW: Google/YouTube Consent Bypass via CDP Cookie-Injection ---
                    # Prevents the detour via consent.youtube.com in 99% of cases
                    cookie_payloads = [
                        {'name': 'CONSENT', 'value': 'YES+cb.20230101-00-p0.de+FX+113', 'domain': '.youtube.com', 'path': '/', 'secure': True},
                        {'name': 'SOCS', 'value': 'CAI', 'domain': '.youtube.com', 'path': '/', 'secure': True},
                        {'name': 'CONSENT', 'value': 'YES+cb.20230101-00-p0.de+FX+113', 'domain': '.google.com', 'path': '/', 'secure': True},
                        {'name': 'SOCS', 'value': 'CAI', 'domain': '.google.com', 'path': '/', 'secure': True},
                        {'name': 'CONSENT', 'value': 'YES+cb.20230101-00-p0.de+FX+113', 'domain': '.google.de', 'path': '/', 'secure': True},
                        {'name': 'SOCS', 'value': 'CAI', 'domain': '.google.de', 'path': '/', 'secure': True}
                    ]
                    for cp in cookie_payloads:
                        try:
                            driver.execute_cdp_cmd('Network.setCookie', cp)
                        except: pass
                    # -------------------------------------------------------------------
                    
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
                        
                        # --- NEW: Consent redirect monitoring & fallback click ---
                        current_url = driver.current_url
                        if "consent.youtube.com" in current_url or "consent.google.com" in current_url:
                            print(f"⚠️ Consent redirect detected ({current_url}). Clicking and waiting for redirect...")
                            try:
                                # Hard JS click that guarantees firing Google's forms
                                driver.execute_script("""
                                    let btns = document.querySelectorAll('button');
                                    for(let b of btns) {
                                        let t = (b.innerText || b.getAttribute('aria-label') || '').toLowerCase();
                                        if(t.includes('akzeptieren') || t.includes('zustimmen') || t.includes('accept') || t.includes('agree') || t === 'alle') {
                                            b.click();
                                            break;
                                        }
                                    }
                                """)
                            except: pass
                            
                            # Wait a maximum of 10 seconds for the URL to return to YouTube
                            wait_start = time.time()
                            while time.time() - wait_start < 10:
                                if "consent." not in driver.current_url:
                                    print("✅ Successfully returned from consent page!")
                                    time.sleep(2) # Wait briefly until YouTube renders layout
                                    break
                                time.sleep(0.5)
                        # ----------------------------------------------------------

                        self.bypass_cookie_banners(driver)
                        time.sleep(2)
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
                safe_wait_time = min(self.sources_cnf.get('wait_time', 3), timeout * 0.05)
                
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
                                    
                                    dict_request["content_type"] = "html"
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
                                safe_wait_time = min(self.sources_cnf.get('wait_time', 3), remaining_time * 0.05)
                                
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