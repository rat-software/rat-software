from .. import app, db
from ..models import Study, ClassificationResult, Result, Scraper
from flask import render_template, flash, redirect, url_for
from flask_security import login_required, current_user
from collections import Counter
from sqlalchemy import func

@app.route('/<id>/analysis')
@login_required
def analysis(id):
    study = Study.query.get_or_404(id)

    classes = ['most_probably_optimized',
               'probably_optimized',
               'most_probably_not_optimized',
               'probably_not_optimized',
               'uncertain',
               'error']

    classification = db.session.query(func.count(Result.id), ClassificationResult.value)\
                               .join(ClassificationResult)\
                               .filter(Result.study == study)\
                               .group_by(ClassificationResult.value).order_by(func.count(Result.id).desc()).all()

    csum = [c[0] for c in classification]
    classes = []

    for c in classification:
        cpct = c[0]/sum(csum)*100
        classes.append([c[1], c[0], cpct])


    dup_total = db.session.query(Result.final_url, func.count(Result.final_url))\
                          .filter(Result.study == study)\
                          .group_by(Result.final_url)\
                          .having(func.count(Result.final_url) > 1)\
                          .count()

    # get url list for each search engine
    # create pairwise comparison between
    bing_q = db.session.query(Result.final_url)\
                       .join(Scraper)\
                       .filter(Result.study == study)\
                       .filter(Scraper.searchengine_id == 2)

    bing = [r.final_url for r in bing_q.all()]


    google_q = db.session.query(Result.final_url)\
                         .join(Scraper)\
                         .filter(Result.study == study)\
                         .filter(Scraper.searchengine_id == 1)

    google = [r.final_url for r in google_q.all()]


    google_org = len(google)
    google_set = set(google)
    google_dup = google_org - len(google_set)

    bing_org = len(bing)
    bing_set = set(bing)
    bing_dup = bing_org - len(bing_set)

    google_only = len(google_set - bing_set)
    bing_only = len(bing_set - google_set)
    overlap = len(google_set.intersection(bing_set))

    total_set = len(google_set.union(bing_set))
    total = len(google + bing)


    return render_template('analysis/analysis.html',
                           study=study,
                           classes=classes,
                           google_org=google_org,
                           google_dup=google_dup,
                           bing_org=bing_org,
                           bing_dup=bing_dup,
                           google_only=google_only,
                           bing_only=bing_only,
                           overlap=overlap,
                           total=total, total_set=total_set)
