from datetime import datetime

timestamp = datetime.now()
timestamp = timestamp.strftime("%d-%m-%Y, %H:%M:%S")

def write_to_log(log):
    f = open("sources.log", "a+")
    f.write(timestamp+": "+log+"\n")
    f.close()
