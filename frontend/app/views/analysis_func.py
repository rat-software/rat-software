from .. import app, db
from ..models import Study, Classifier, ClassifierResult, Result, Scraper, Answer
from collections import Counter
from itertools import combinations
from sqlalchemy import func
from ..helpers import percentage_calc
from sqlalchemy import text

def get_seo_classification(study):
    """
    Retrieves SEO classification statistics for a given study based on the classifiers.

    Args:
        study (Study): The study for which SEO classification is being retrieved.

    Returns:
        list: A list of dictionaries where each dictionary represents an SEO classification label and its statistics.
    """
    
    if study.classifier:
        seo_classes = []
    else:
        seo_classes = None

    vals = []

    # Process each classifier associated with the study
    for clf in study.classifier:

        id_study = study.id
        
        clfs = db.session.execute(text("SELECT MIN(classifier_result.id) AS classifier_result_id, result.id, MIN(classifier_result.value) AS classifier_result_value, result.url, result.main, MIN(classifier_result.created_at) AS created_at FROM classifier_result JOIN result ON classifier_result.result = result.id WHERE result.study = :id_study AND classifier_result.classifier = 1 GROUP BY result.id, result.url, result.main;"), {'id_study': str(id_study)})

        for c in clfs:
            vals.append(c[2])        

        max = len(vals)

        
        # Define SEO classification labels
        seo_labels = ["most_probably_optimized", "probably_optimized",
                      "probably_not_optimized", "most_probably_not_optimized", "error"]

        # Calculate the count and percentage for each SEO label
        for label in seo_labels:
            line = {"label": label.replace("_", " ").capitalize(),
                    "value": vals.count(label),
                    "pct": vals.count(label) / max}
            seo_classes.append(line)
    return seo_classes


def get_result_stats(study):
    """
    Computes the statistics related to results collection for a given study.

    Args:
        study (Study): The study for which result statistics are being computed.

    Returns:
        dict: A dictionary containing various statistics about the results collection process.
    """
    # Retrieve all scrapers associated with the study
    scrapers = db.session.query(Scraper).filter(Scraper.study == study)

    # Count scrapers that have completed their progress
    scrapers_done = scrapers.filter(Scraper.progress == 1).count()
    # Count all scrapers
    scrapers_all = scrapers.count()
    # Calculate the percentage of scrapers that have completed progress
    scraper_stat = percentage_calc(scrapers_done, scrapers_all, "str")

    # Prepare result statistics
    result_stats = {}
    result_stats["Queries"] = len(study.queries)
    result_stats["Search Engines"] = len(study.searchengines)
    result_stats["Results to Collect per Query"] = study.result_count
    result_stats["Collection Status"] = scraper_stat

    return result_stats


def get_evaluation_stats(study):
    """
    Computes the statistics related to evaluations for a given study.

    Args:
        study (Study): The study for which evaluation statistics are being computed.

    Returns:
        dict: A dictionary containing various statistics about the evaluation process.
    """
    # Retrieve all evaluations associated with the study
    evals = db.session.query(Answer).filter(Answer.study == study)

    # Count evaluations that have been completed
    evals_done = evals.filter(Answer.status == 1).count()
    # Count all evaluations
    evals_all = evals.count()
    # Calculate the percentage of completed evaluations
    evals_stat = percentage_calc(evals_done, evals_all, "str")

    # Prepare evaluation statistics
    evaluation_stats = {}
    evaluation_stats["Participants"] = len(study.participants)
    evaluation_stats["Questions"] = len(study.questions)
    evaluation_stats["Evaluations per Participant"] = len(study.results) * len(study.questions)
    evaluation_stats["Evaluation Status"] = evals_stat

    return evaluation_stats
