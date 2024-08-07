#!/usr/bin/env python
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This example generates keyword ideas from a list of seed keywords."""


import argparse
import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# importing module
import sys
import os
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
moduledir = parentdir + "/app/"

google_ads_client = parentdir+"/google_ads/google-ads.yaml"


sys.path.append(moduledir)

customer_id = "your_customer_id" #change the id according to your google ads account

#importing required module
from db import *


# import db library from the flask app
if sys.argv[1]:
    study_id = str(sys.argv[1])
    keywords = get_keywords(study_id)

    if keywords:
        for k in keywords:
            keyword_id = k['keyword_id']
            status = 0

            if get_keyword_status(keyword_id, status):
                status = 2
                update_keyword_status(status, keyword_id)

        for k in keywords:
            keyword_id = k['keyword_id']
            status = 2

            if get_keyword_status(keyword_id, status):
            
                keyword_texts = [k['keyword']]
                location_ids = [k['region_criterion_id']]
                language_id = k['language_criterion_id']
                page_url = ""           


            # [START generate_keyword_ideas]
                def main(
                    client, customer_id, location_ids, language_id, keyword_texts, page_url
                ):
                    keyword_plan_idea_service = client.get_service("KeywordPlanIdeaService")
                    keyword_competition_level_enum = (
                        client.enums.KeywordPlanCompetitionLevelEnum
                    )
                    keyword_plan_network = (
                        client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH_AND_PARTNERS
                    )
                    location_rns = map_locations_ids_to_resource_names(client, location_ids)
                    language_rn = client.get_service("GoogleAdsService").language_constant_path(
                        language_id
                    )

                    # Either keywords or a page_url are required to generate keyword ideas
                    # so this raises an error if neither are provided.
                    if not (keyword_texts or page_url):
                        raise ValueError(
                            "At least one of keywords or page URL is required, "
                            "but neither was specified."
                        )

                    # Only one of the fields "url_seed", "keyword_seed", or
                    # "keyword_and_url_seed" can be set on the request, depending on whether
                    # keywords, a page_url or both were passed to this function.
                    request = client.get_type("GenerateKeywordIdeasRequest")
                    request.customer_id = customer_id
                    request.language = language_rn
                    request.geo_target_constants = location_rns
                    request.include_adult_keywords = False
                    request.keyword_plan_network = keyword_plan_network

                    # To generate keyword ideas with only a page_url and no keywords we need
                    # to initialize a UrlSeed object with the page_url as the "url" field.
                    if not keyword_texts and page_url:
                        request.url_seed.url = page_url

                    # To generate keyword ideas with only a list of keywords and no page_url
                    # we need to initialize a KeywordSeed object and set the "keywords" field
                    # to be a list of StringValue objects.
                    if keyword_texts and not page_url:
                        request.keyword_seed.keywords.extend(keyword_texts)

                    # To generate keyword ideas using both a list of keywords and a page_url we
                    # need to initialize a KeywordAndUrlSeed object, setting both the "url" and
                    # "keywords" fields.
                    if keyword_texts and page_url:
                        request.keyword_and_url_seed.url = page_url
                        request.keyword_and_url_seed.keywords.extend(keyword_texts)

                    keyword_ideas = keyword_plan_idea_service.generate_keyword_ideas(
                        request=request
                    )


                    

                    for idea in keyword_ideas:
                        competition_value = idea.keyword_idea_metrics.competition.name

                        keyword_idea = idea.text

                        avg_monthly_searches = int(idea.keyword_idea_metrics.avg_monthly_searches)

                        competition = competition_value

                        insert_keyword_idea(study_id, keyword_id, keyword_idea, avg_monthly_searches, competition)

                        print(
                            f'Keyword idea text "{idea.text}" has '
                            f'"{idea.keyword_idea_metrics.avg_monthly_searches}" '
                            f'average monthly searches and "{competition_value}" '
                            "competition.\n"
                        )
                    # [END generate_keyword_ideas]

                    status = 1
                    update_keyword_status(status, keyword_id)


                def map_locations_ids_to_resource_names(client, location_ids):
                    """Converts a list of location IDs to resource names.

                    Args:
                        client: an initialized GoogleAdsClient instance.
                        location_ids: a list of location ID strings.

                    Returns:
                        a list of resource name strings using the given location IDs.
                    """
                    build_resource_name = client.get_service(
                        "GeoTargetConstantService"
                    ).geo_target_constant_path
                    return [build_resource_name(location_id) for location_id in location_ids]


                if __name__ == "__main__":
                    # GoogleAdsClient will read the google-ads.yaml configuration file in the
                    # home directory if none is specified.
                    #googleads_client = GoogleAdsClient.load_from_storage(version="v16")
                    googleads_client = GoogleAdsClient.load_from_storage(google_ads_client)



                    try:
                        main(
                            googleads_client,
                            customer_id,
                            location_ids,
                            language_id,
                            keyword_texts,
                            page_url,
                        )
                    except GoogleAdsException as ex:
                        print(
                            f'Request with ID "{ex.request_id}" failed with status '
                            f'"{ex.error.code().name}" and includes the following errors:'
                        )
                        for error in ex.failure.errors:
                            print(f'\tError with message "{error.message}".')
                            if error.location:
                                for field_path_element in error.location.field_path_elements:
                                    print(f"\t\tOn field: {field_path_element.field_name}")
                        sys.exit(1)
