"""
Library for checking if proxies are working and getting a working proxy.
"""
import requests
import time
import random
import csv
import os
import inspect

def check_proxy(proxy, test_url="https://www.google.com", timeout=10):
    """
    Check if a proxy is working by making a request to a test URL.
    
    Args:
        proxy (str): Proxy string in the format 'ip:port' or 'user:pass@ip:port'
        test_url (str): URL to test the proxy against
        timeout (int): Request timeout in seconds
        
    Returns:
        bool: True if proxy is working, False otherwise
    """
    print(f"Testing proxy: {proxy}")
    try:
        # Format the proxy for the requests library
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        
        # Make a request with the proxy
        start_time = time.time()
        response = requests.get(
            test_url, 
            proxies=proxies, 
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
            },
            verify=False  # Skip SSL verification to avoid certificate issues with some proxies
        )
        
        # Check if the request was successful
        request_time = time.time() - start_time
        if response.status_code == 200:
            print(f"Proxy {proxy} is working (response time: {request_time:.2f}s)")
            return True
        else:
            print(f"Proxy {proxy} returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Proxy {proxy} failed: {str(e)}")
        return False

def get_working_proxy(country_proxy, max_attempts=3):
    """
    Try to find a working proxy from a country's proxy list.
    
    Args:
        country_proxy (str): Country code for the proxy file (e.g., 'USA')
        max_attempts (int): Maximum number of proxies to try before giving up
        
    Returns:
        tuple: (proxy, error_code) where proxy is a working proxy string or None if none work,
               and error_code is an error message if no proxies work
    """
    # Initialize the list for proxies
    proxies = []
    error_code = ""
    
    print(f"Searching for working proxy in country: {country_proxy}")
    
    # Get the directory path to locate the proxy file
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    
    csv_file = country_proxy + ".csv"
    csv_path = os.path.join(parentdir, 'proxies', csv_file)
    
    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        error_msg = f"Proxy file not found: {csv_file}"
        print(error_msg)
        return None, error_msg
    
    # Load proxies from a CSV file
    try:
        with open(csv_path) as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',')
            for row in csv_reader:
                if row:  # Check if row is not empty
                    proxies.append(row[0])
        
        print(f"Loaded {len(proxies)} proxies from {csv_file}")
    except Exception as e:
        error_msg = f"Failed to read proxy file {csv_file}: {str(e)}"
        print(error_msg)
        return None, error_msg
    
    if not proxies:
        error_msg = f"No proxies found in {csv_file}"
        print(error_msg)
        return None, error_msg
    
    # Shuffle the proxies for random selection
    random.shuffle(proxies)
    
    # Try proxies until we find a working one or reach max_attempts
    attempts = 0
    tested_proxies = []
    
    for proxy in proxies:
        if attempts >= max_attempts and len(proxies) > max_attempts:
            break
            
        attempts += 1
        tested_proxies.append(proxy)
        
        if check_proxy(proxy):
            return proxy, ""
        
        # Small delay between attempts
        time.sleep(1)
    
    # If we get here, no proxies worked
    error_code = f"All proxies failed after {attempts} attempts. Tested: {', '.join(tested_proxies[:5])}"
    if len(tested_proxies) > 5:
        error_code += f" and {len(tested_proxies) - 5} more"
    
    print(error_code)
    return None, error_code
def get_proxy_for_scraping(country_proxy, country):
    """
    Get a working proxy for scraping based on the country.
    
    Args:
        country_proxy (str): Country code for the proxy
        country (str): Current country setting
        
    Returns:
        tuple: (proxy, error_code) where proxy is a working proxy string or None,
               and error_code is an error message if no proxies work
    """
    # If country_proxy is different from the current country, use a proxy
    if country_proxy != country and country_proxy is not None:
        return get_working_proxy(country_proxy)
    else:
        # No proxy needed
        return None, ""
