from .. import app, db
from ..models import Study, Classifier, ClassifierResult, Result, Scraper, Answer
from collections import Counter
from itertools import combinations
from sqlalchemy import func
from ..helpers import percentage_calc


def get_seo_classification(study):
    if study.classifier:
        seo_classes = []
    else:
        seo_classes = None

    for clf in study.classifier:
        clfs = db.session.query(ClassifierResult).filter(
            ClassifierResult.classifier == clf).all()

        # sql filter does not work // buggy, hence the manual filter
        clfs = [c for c in clfs if c.result in study.results]
        vals = [c.value for c in clfs]
        max = len(vals)

        seo_labels = ["most_probably_optimized", "probably_optimized",
                "probably_not_optimized", "most_probably_not_optimized", "error"]
        for label in seo_labels:
            line = {"label": label.replace("_", " ").capitalize(),
                        "value": vals.count(label),
                        "pct": vals.count(label) / max}
            seo_classes.append(line)
    return seo_classes


def get_result_stats(study):
    scrapers = db.session.query(Scraper).filter(Scraper.study == study)

    scrapers_done = scrapers.filter(Scraper.progress == 1).count()
    scrapers_all = scrapers.count()
    scraper_stat = percentage_calc(scrapers_done, scrapers_all, "str")

    result_stats = {}
    result_stats["Queries"] = len(study.queries)
    result_stats["Search Engines"] = len(study.searchengines)
    result_stats["Results to Collect per Query"] = study.result_count
    result_stats["Collection Status"] = scraper_stat

    return result_stats


def get_evaluation_stats(study):
    evals = db.session.query(Answer).filter(Answer.study == study)

    evals_done = evals.filter(Answer.status == 1).count()
    evals_all = evals.count()
    evals_stat = percentage_calc(evals_done, evals_all, "str")

    evaluation_stats = {}
    evaluation_stats["Participants"] = len(study.participants)
    evaluation_stats["Questions"] = len(study.questions)
    evaluation_stats["Evaluations per Participant"] = len(
        study.results) * len(study.questions)
    evaluation_stats["Evaluation Status"] = evals_stat

    return evaluation_stats
