from lib_db import *
from lib_sources import *
from lib_log import *

from datetime import datetime

import json

import time

import threading


def file_to_dict(path):
    f = open(path, encoding="utf-8")
    dict = json.load(f)
    f.close()
    return dict

result_dict_available = threading.Event()
final_url_available = threading.Event()

def scrape_url(url):
    global result_dict
    result_dict = save_code(url)
    result_dict_available.set()


def get_final_url_check(url):
    global final_url_check
    try:
        final_url_check = get_real_url(url)
    except:
        try:
            final_url = get_real_url_request(url)
        except:
            final_url = url
    final_url_available.set()

sources_cnf = file_to_dict("config_sources.ini")

write_to_log("Next \t \t Job\t ")

sources_null = get_sources()

for source_to_scrape in sources_null:
    result_id = source_to_scrape[0]
    url = source_to_scrape[1]

    print(url)

    progress = 2

    created_at = datetime.now()

    job_server = sources_cnf['job_server']

    if check_progress(url, result_id):
        pass
    else:

        try:

            source_id_check = get_source_check(url)

            if not source_id_check:

                thread = threading.Thread(target=get_final_url_check(url))
                thread.start()

                # wait here for the result to be available before continuing
                final_url_available.wait()

                if final_url_check:
                    source_id_check = get_source_check_final_url(final_url_check)
                else:
                    source_id = insert_source(url, -1, created_at, result_id, job_server)

            if source_id_check:
                print("if so")

                log = str(source_id_check)+"_"+str(result_id)+"\t"+url+"\tupdate result"

                write_to_log(log)

                if get_result_content(source_id_check):
                    print("update result")
                    rc = get_result_content(source_id_check)
                    ip = rc[0]
                    main = rc[1]
                    final_url = rc[2]
                    update_result(result_id, source_id_check, ip, main, final_url)

            else:

                if not get_source_check_by_result_id(result_id):
                    source_id = insert_source(url, progress, created_at, result_id, job_server)
                    source_id = source_id[0]
                else:
                    source_id = False

                #print("insert new source")


                if source_id:

                    try:
                        thread = threading.Thread(target=scrape_url(url))
                        thread.start()

                        # wait here for the result to be available before continuing
                        result_dict_available.wait()

                        code = result_dict['code']
                        bin = result_dict['bin']
                        content_type = result_dict['request']['content_type']
                        status_code = result_dict['request']['status_code']
                        final_url = result_dict['final_url']
                        ip = result_dict['meta']['ip']
                        main = result_dict['meta']['main']
                        error_code = result_dict['error_codes']

                        #print(result_dict['final_url'])

                        if len(error_code) == 0:
                            progress = 1
                        else:
                            progress = -1

                        if content_type == 'error':
                            progress = -1
                            print("content_type:error")

                        try:
                            update_source(source_id, code, bin, progress, content_type, error_code, status_code, final_url, created_at)
                            update_result(result_id, source_id, ip, main, final_url)

                        except Exception as e:
                            write_to_log("Updating source table failed \t \t \t"+str(e))
                            write_to_log(log)

                        log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code

                        write_to_log(log)

                    except Exception as e:
                        error_code = "Source scraping failed: "+str(e)
                        error = "error"
                        progress = -1
                        status_code = -1
                        log = str(source_id)+"_"+str(result_id)+"\t"+url+"\t"+str(progress)+"\t"+error_code
                        write_to_log(log)
                        update_source(source_id, error, error, progress, error, error_code, status_code, error, created_at)


        except Exception as e:
            print(str(e))
            log = "Skipped Result:"+str(result_id)+"\t \t \t "
            write_to_log(log)
