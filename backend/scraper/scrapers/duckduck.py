import datetime

from lib.sources import get_real_url


from log import *

scraper_id = 0
reset_id = 0

search_engine = "duckduckgo.se"


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common import proxy
import time

import pickle

import os
current_path = os.path.abspath(os.getcwd())

import csv

queries = "malte_queries.csv"

with open(queries, encoding='utf-8') as csv_file:
    csv_reader = csv.reader(csv_file, quotechar="'", delimiter='\t')
    for row in csv_reader:
        query_id = row[0]
        query = row[1]
        print(query_id)
        print(query)

        timestamp = datetime.datetime.now()
        timestamp = timestamp.strftime("%d-%m-%Y, %H:%M:%S")

        write_to_log(timestamp, "Scrape "+str(search_engine)+" Job_Id:"+str(scraper_id)+" Query:"+str(query)+" started")

        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.firefox.options import Options
        import time

        from lxml import html
        from bs4 import BeautifulSoup

        def get_search_results(driver):
            source = driver.page_source
            tree = html.fromstring(source)
            found_urls = tree.xpath("//div[@class='ikg2IXiCD14iVX7AdZo1']/h2/a/@href")
            found_titles = tree.xpath("//div[@class='ikg2IXiCD14iVX7AdZo1']/h2/a/span/text()")
            redirect = "false"
            titles_urls = []
            i = 0
            for f_url in found_urls:
                if redirect == "true":
                    url = get_real_url(f_url)
                else:
                    url = f_url
                titles_urls.append([url, found_titles[i]])
                i = i + 1

            return titles_urls

        import os
        current_path = os.path.abspath(os.getcwd())

        if os.name == "nt":
            extension_path = current_path+"\i_dont_care_about_cookies-3.4.0.xpi"

        else:
            extension_path = current_path+"/i_dont_care_about_cookies-3.4.0.xpi"

        options = Options()
        options.headless = True

        driver = webdriver.Firefox(options=options)
        driver.install_addon(extension_path, temporary=False)

        url = "https://duckduckgo.com/?q="+query+"&kp=-1&kl=se-sv&ia=web"

        print(url)

        driver.get(url)
        search_results = []
        search_results = get_search_results(driver)

        driver.quit()

        import datetime
        from datetime import date
        today = date.today()
        timestamp = datetime.datetime.now()

        from urllib.parse import urlsplit
        from urllib.parse import urlparse
        import socket

        def get_meta(url):
            meta = []
            try:
                parsed_uri = urlparse(url)
                hostname = '{uri.netloc}'.format(uri=parsed_uri)
                ip = socket.gethostbyname(hostname)
            except:
                ip = "-1"

            main = '{0.scheme}://{0.netloc}/'.format(urlsplit(url))
            meta = [ip, main]
            return meta

        position = 1
        result = ""

        for url_title in search_results:

            created_at = datetime.datetime.now()

            url = url_title[0]
            title = url_title[1]

            meta = get_meta(url)

            ip = meta[0]
            main_url = meta[1]

            result = str(query_id)+"\t"+str(query)+"\t"+str(position)+"\t"+str(url)+"\t"+str(main_url)+"\t"+str(title)+"\t"+str(ip)+"\t"+str(created_at)

            f = open("malte_results_duckduckgo.csv", "a+", encoding='utf-8')
            f.write(result+"\n")
            f.close()

            position+=1
