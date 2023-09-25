from datetime import datetime

class Logger:

    def __init__(self):
        self = self

    def __del__(self):
        print('Logger object destroyed')

    def write_to_log(self, log):
        timestamp = datetime.now()
        timestamp = timestamp.strftime("%d-%m-%Y, %H:%M:%S")
        f = open("sources_scraper.log", "a+")
        f.write(timestamp+": "+log+"\n")
        f.close()
