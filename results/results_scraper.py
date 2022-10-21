import psycopg2
from psycopg2.extras import execute_values
from psycopg2.errors import UniqueViolation

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

from bs4 import BeautifulSoup

import json, os, time, logging, base64, argparse, urllib.parse
from pathlib import Path
from datetime import datetime

# load config
f = open('config.ini', encoding="utf-8")
config = json.load(f)
f.close()


# connect to server db
db_conn = config["db_conn"]

conn = psycopg2.connect(**db_conn)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def buildURL(q, se, l, c, lang, mkt, setLang, kl, m):
    if se == "Google":

        main = "https://www.google.com/search?"
        query = "q=" + q
        limit = "num=" + str(l)
        country = "cr=country" + c
        lang = "lr=" + lang

        url = "&".join([main, query, limit, country, lang])

    elif se == "Bing":

        main = "https://www.bing.com/search?"
        query = "q=" + q
        limit = "count=" + str(l)
        country = "mkt=" + mkt
        lang = "setLang=" + setLang


        url = "&".join([main, query, limit, country, lang])

    elif se == "DuckDuckGo":

        main = "https://duckduckgo.com/?"
        query = "q=" + q
        country = "kl=" + kl
        full = "kaf=" + str(1)

        url = "&".join([main, query, country, full])

    elif se == "Metager":

        main = "https://metager.de/meta/meta.ger3?"
        query = "eingabe=" + q
        focus = "focus=" + "web"
        country = "m=" + m


        url = "&".join([main, query, focus, country])

    else:
        url = ""

    return url

# start selenium
driver = webdriver.Firefox()
add_on = str(Path().absolute()) + config["add_on_path"]
driver.install_addon(add_on)


# set parameters for url builder
args = {
    "c": "DE",
    "lang": "lang_de",
    "mkt": "de-DE",
    "setLang": "DE",
    "kl": "de-de",
    "m": "gg"
}

# get one open scraper
cur.execute("select * from scraper where progress = 0")
scraper = cur.fetchone()

# get all scrapers of the same study
cur.execute("select * from scraper where progress = 0 and study = %s limit %s", (scraper['study'], config["scraper_limit"],))
scrapers = cur.fetchall()

# iterate over all scrapers
for s in scrapers:

    # get query
    cur.execute("select * from query where id = %s", (s["query"],))
    query = cur.fetchone()

    # get search engine
    cur.execute("select * from searchengine where id = %s", (s["searchengine"],))
    search_engine = cur.fetchone()

    #########################

    # set more parameters for url builder
    q = query["query"]
    se = search_engine["name"]
    limit = 20

    # build url
    url = buildURL(q, se, limit, **args)

    # call url
    driver.get(url)
    time.sleep(2)

    #########################

    # get serp
    code = driver.page_source
    code = base64.b64encode(code.encode("utf-8"))

    img = driver.get_full_page_screenshot_as_base64()

    # save serp to db; return id of serp for results
    sql = """insert into serp (page, code, img, progress, created_at, scraper, query)
             values (%s, %s, %s, %s, %s, %s, %s) returning id"""

    data = (1, code, img, 1, datetime.now(), s['id'], s['query'], )
    cur.execute(sql, data)
    conn.commit()

    serp = cur.fetchone()

    #########################

    # load config to parse results
    path = str(Path().absolute()) + config["config_path"] + search_engine["config"]
    f = open(path, encoding="utf-8")
    cnf = json.load(f)
    f.close()

    #########################

    # parse results
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    results = soup.select(cnf["result"])

    pos = 0

    for r in results:
        pos += 1

        if pos <= 10:

            # get title
            try:
                title = r.select(cnf["result_title"])[0].text.strip()
            except IndexError:
                title = "N/A"

            # get description
            try:
                desc = r.select(cnf["result_description"])[0].text.strip()
            except IndexError:
                desc = "N/A"

            # get url
            try:
                url = r.select(cnf["result_url"])[0]["href"]
            except IndexError:
                url = "N/A"

            # get domain url
            parsed = urllib.parse.urlparse(url)
            main = parsed.netloc

            # sql insert statement
            sql = """insert into result
                     (title, description, url, position, created_at,
                     main, imported, resulttype, scraper, serp, query, study)
                     values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                     returning id"""
            data = (title, desc, url, pos, datetime.now(),
                    main, False, 2, s['id'], serp['id'], s['query'], s['study'], )

            cur.execute(sql, data)
            conn.commit()

    # set scraper to complete
    cur.execute("update scraper set progress = 1 where id = %s", (s["id"],))
    conn.commit()

    #time.sleep(2)
driver.close()
