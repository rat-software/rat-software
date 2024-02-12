from libs.lib_scraping import *

def test_scraper(query, limit, scraper, headless):
    search_results = run(query, limit, scraper, headless)

    i = 0
    if search_results != -1:
        for sr in search_results:
            i+=1
            print(i)
            print(sr[0])
            print(sr[1])
            print(sr[2])
    else:
        print("Scraping test failed")


#Test

# from scrapers.google_se import *
#
# google_se = Scraping()
#
# test_scraper("xbox", 20, google_se, 1)
# test_scraper("hamburg", 20, google_de, 0)
# test_scraper("berlin", 20, google_de, 0)
# test_scraper("katzenfutter", 20, google_de, 0)
# test_scraper("ipads", 20, google_de, 0)

#Test SUB Hamburg Books

# from scrapers.katalogplus_de_articles import *
#
# sub_books_de = Scraping()
#
# test_scraper("neurologie", 30, sub_books_de, 0)

#from scrapers.ecosia_de import *

#ecosia_de = Scraping()

#test_scraper("trinkwasser", 10, ecosia_de, 1)

# from scrapers.bing_de import *
# bing_de = Scraping()
# test_scraper("trinkwasser", 10, bing_de, 1)

#from scrapers.google_us_new import *

#google_us_new = Scraping()

#test_scraper("till lindemann", 20, google_us_new, 0)

# from scrapers.google_ee import *
#
# google_ee = Scraping()
#
# test_scraper("till lindemann", 20, google_ee, 1)
#
# from scrapers.google_se import *
#
# google_se = Scraping()
#
# test_scraper("till lindemann", 20, google_se, 0)
#
# from scrapers.google_news_mx import *

# google_news_mx = Scraping()

# test_scraper("rammstein", 20, google_news_mx, 0)


# from scrapers.dogpile import *

# dogpile = Scraping()

# test_scraper("trinkwasser", 20, dogpile, 0)

#from scrapers.test import *

from scrapers.brave_de import *

brave_de = Scraping()

test_scraper("korg", 30, brave_de, True)

