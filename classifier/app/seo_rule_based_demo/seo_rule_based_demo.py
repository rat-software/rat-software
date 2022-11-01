from seo_rule_based_demo.seo_rule_based_indicators_demo import *

from classifier_db_lib import *

classifier = "seo_rule_based_demo"

def main():

    values = get_values(classifier)

    for value in values:

        result = value['id']

        insert_classification_result(classifier, "in process", result)

    for value in values:
        raw_data = {}

        for k,v in value.items():

            raw_data.update({k: v})

        result = raw_data["id"]

        print(result)


        url = raw_data["url"]

        print(url)

        main = raw_data["main"]
        position = raw_data["position"]
        searchengine = raw_data["searchengine"]
        searchengine_title = raw_data["title"]
        searchengine_description = raw_data["description"]
        ip = raw_data["ip"]
        source = raw_data["source"]
        code = decode_code(raw_data["code"])

        #limit number of characters for demo purposes

        # if len(code) > 300000:
        #     cutoff = - 300000 + len(code)
        #     code = code[:-cutoff]

        #picture = decode_picture(raw_data["bin"])
        content_type = raw_data["content_type"]
        error_code = raw_data["error_code"]
        status_code = raw_data["status_code"]
        final_url = raw_data["final_url"]
        query = raw_data["query"]


        try:

            if status_code == 200 and len(error_code) == 0 and code != 'decoding error':


                indicators = {}

                #print("\n identify plugins")

                plugins = identify_plugins(code)



                indicators.update({'tools analytics': plugins['tools analytics']})
                indicators.update({'tools seo': plugins['tools seo']})
                indicators.update({'tools caching': plugins['tools caching']})
                indicators.update({'tools social': plugins['tools social']})
                indicators.update({'tools ads': plugins['tools ads']})


                #print("\n identify_sources")

                tools_analytics = len(plugins['tools analytics'])
                tools_seo = len(plugins['tools seo'])
                tools_caching = len(plugins['tools caching'])
                tools_social = len(plugins['tools social'])
                tools_ads = len(plugins['tools ads'])

                lists = identify_sources(main)

                indicators.update({'ads': lists['ads']})
                indicators.update({'company': lists['company']})
                indicators.update({'seo_customers': lists['seo_customers']})
                indicators.update({'news': lists['news']})
                indicators.update({'not_optimized': lists['not_optimized']})
                indicators.update({'search_engine_services': lists['search_engine_services']})
                indicators.update({'shops': lists['shops']})



                sources_ads = len(lists['ads'])
                sources_company = len(lists['company'])
                sources_customers = len(lists['seo_customers'])
                sources_news = len(lists['news'])
                sources_not_optimized = len(lists['not_optimized'])
                sources_services = len(lists['search_engine_services'])
                sources_shops = len(lists['shops'])

                #print("\n robots.txt")

                #robots_txt = identify_robots_txt(main)

                #indicators.update({'robots_txt': robots_txt})

                #print("\n loading_time")

                #loading_time = calculate_loading_time(url)

                #indicators.update({'loading_time': loading_time})

                #print("\n hyperlinks")

                hyperlinks = identify_hyperlinks(get_hyperlinks(code, main), main)

                internal_links = hyperlinks["internal"]

                indicators.update({'internal_links': internal_links})

                external_links = hyperlinks["external"]

                indicators.update({'external_links': external_links})

                #print("\n url length")

                url_length = identify_url_length(url)

                indicators.update({'url_length': url_length})

                #print("\n https")

                https = identify_https(url)

                indicators.update({'https': https})

                #print("\n micros")

                micros_list = identify_micros(code)

                indicators.update({'micros': micros_list})

                micros = len(micros_list)

                print("\n sitemap")

                sitemap = identify_sitemap(code)

                indicators.update({'sitemap': sitemap})

                print("\n og")

                og = identify_og(code)

                indicators.update({'og': og})

                print("\n viewport")

                viewport = identify_viewport(code)

                indicators.update({'viewport': viewport})

                print("\n wordpress")

                wordpress = identify_wordpress(code)

                indicators.update({'wordpress': wordpress})

                print("\n canonical")

                canonical = identify_canonical(code)

                indicators.update({'canonical': canonical})

                print("\n nofollow")

                nofollow = identify_nofollow(code)

                indicators.update({'nofollow': nofollow})

                h1 = identify_h1(code)

                indicators.update({'h1': h1})

                if query:
                    keywords_in_code = identify_keywords_in_source(code, query)
                    keywords_in_url = identify_keywords_in_url(url, query)
                    keyword_density = identify_keyword_density(code, query)

                else:
                    keywords_in_code = -1
                    keywords_in_url = -1
                    keyword_density = -1

                #print("\n keywords")

                indicators.update({'keywords_in_code': keywords_in_code})
                indicators.update({'keywords_in_url': keywords_in_url})
                indicators.update({'keyword_density': keyword_density})

                #print("\n description")

                description = identify_description(code)

                indicators.update({'description': description})

                #print("\n title")

                title = identify_title(code)

                indicators.update({'title': title})

                for key, ind in indicators.items():

                    if type(ind) != list and type(ind) is not dict:
                        indicator = key
                        insert_result = str(ind)
                        insert_indicator(indicator, insert_result, classifier, result)
                    else:
                        if (type(ind) is list):
                            indicator = key
                            insert_result = ", ".join(ind)
                            insert_indicator(indicator, insert_result, classifier, result)

                        if (type(ind) is dict):
                            for k, v in ind.items():
                                indicator = k
                                insert_result = v
                                if (type(v) is list):
                                    insert_result = ", ".join(v)
                                else:
                                    insert_result = str(v)

                                insert_indicator(indicator, insert_result, classifier, result)

                #classify the result
                optimized = 0
                probably_optimized = 0
                probably_not_optimized = 0
                classification_result = "uncertain"

                #most probably optimized
                if tools_seo > 0 or sources_customers > 0 or sources_news > 0 or sources_ads > 0 or micros > 0:
                    optimized = 1
                    classification_result = 'most_probably_optimized'

                #probably optimized
                if optimized == 0 and (tools_analytics > 0 or sources_shops > 0 or sources_company > 0 or viewport == 1 or sitemap == 1 or nofollow > 0 or canonical > 0):
                    probably_optimized = 1
                    classification_result = 'probably_optimized'

                #probably_not_optimized
                if (title == 0 or description == 0) and og == 0:
                    classification_result = 'probably_not_optimized'

                if sources_not_optimized > 0:
                    classification_result = 'most_probably_not_optimized'

            else:
                classification_result = 'error'

        except Exception as e:
            print(str(e))
            classification_result = 'error'

        print(classification_result)


        update_classification_result(classifier, classification_result, result)
