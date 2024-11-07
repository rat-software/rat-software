from .. import app, db
from ..models import Study, ClassifierIndicator, Classifier, Result, Scraper
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_security import login_required, current_user
from collections import Counter
from sqlalchemy import func
from itertools import combinations
from .analysis_func import get_seo_classification, get_result_stats, get_evaluation_stats
#bp = Blueprint('analysis', __name__)

@app.route('/<id>/analysis')
@login_required
def analysis(id):
    """
    Renders the analysis page for a specific study, including SEO classification,
    result statistics, and evaluation statistics. Computes the overlap of final URLs
    between different search engines if there are multiple search engines in the study.

    Args:
        id (str): The ID of the study.

    Returns:
        Rendered HTML template for the analysis page.
    """
    # Retrieve the study from the database or return a 404 error if not found
    study = Study.query.get_or_404(id)

    # Get SEO classification for the study
    try:
        classes = get_seo_classification(study)
        classes = classes[:5]
    except:
        classes = ""

    
    


    # Get result statistics for the study
    result_stats = get_result_stats(study)

    # Get evaluation statistics for the study
    evaluation_stats = get_evaluation_stats(study)

    # Check if there are multiple search engines for overlap analysis
    if len(study.searchengines) > 1:
        # Get all final URLs that appear more than once
        dup_total = db.session.query(Result.final_url, func.count(Result.final_url))\
                              .filter(Result.study == study)\
                              .group_by(Result.final_url)\
                              .having(func.count(Result.final_url) > 1)\
                              .count()

        # Initialize a dictionary to hold URLs and counts for each search engine
        se_list = {}

        # Iterate over each search engine to gather URL data
        for se in study.searchengines:
            # Query for final URLs related to the search engine
            q = db.session.query(Result.final_url)\
                          .join(Scraper)\
                          .filter(Result.study == study)\
                          .filter(Scraper.searchengine_id == se.id)

            # Create a list of URLs and calculate counts
            urls = [r.final_url for r in q.all()]
            count = len(urls)
            url_set = set(urls)
            dup_count = count - len(url_set)

            # Store results in the dictionary
            se_list[se.name] = {"Urls": urls,
                                "Total count": count,
                                "Duplicate count": dup_count,
                                "Sources": url_set}

        # Compute overlap between pairs of search engines
        overlap_list = []
        pairs = list(map(dict, combinations(se_list.items(), 2)))
        for p in pairs:
            se_keys = list(p.keys())
            se_1 = se_list[se_keys[0]]
            se_2 = se_list[se_keys[1]]

            # Create a key for the pair
            k = "-".join(p.keys())

            # Calculate differences and overlap between the two search engines
            only_1 = len(se_1["Sources"] - se_2["Sources"])
            only_2 = len(se_2["Sources"] - se_1["Sources"])
            overlap = len(se_1["Sources"].intersection(se_2["Sources"]))
            total = len(se_1["Sources"] | se_2["Sources"])

            # Store results in the list
            overlap = {"SE_Pair": k,
                       "SE_1": se_keys[0],
                       "SE_1 exclusive": only_1,
                       "SE_2": se_keys[1],
                       "SE_2 exclusive": only_2,
                       "Overlap": overlap,
                       "Total": total}

            overlap_list.append(overlap)
    else:
        # If only one search engine, set overlap list to None
        overlap_list = None

    # Render the analysis page with the computed data
    return render_template('analysis/analysis.html',
                           study=study,
                           result_stats=result_stats,
                           evaluation_stats=evaluation_stats,
                           overlap_list=overlap_list,
                           classes=classes)
