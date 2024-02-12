from bs4 import BeautifulSoup
from lxml import html

f = open("scraper_test.html", "r", encoding="utf-8", errors="replace")
print(f.read())