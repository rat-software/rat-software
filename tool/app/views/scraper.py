from .. import app, db
from ..models import Study, Scraper
from flask import render_template, flash, redirect, url_for
from flask_security import login_required, current_user
from datetime import datetime


@app.route('/study/<id>/run')
@login_required
def run_study(id):
    # set scraper/study status to running
    study = Study.query.get_or_404(id)

    study.status = 3
    study.updated_at = datetime.now()

    # create scraper for each search engine and each query
    scrapers_ = []

    for query in study.queries:
        for searchengine in study.searchengines:
            scraper = Scraper()

            scraper.progress = 0
            scraper.counter = 0
            scraper.limit = study.result_count
            scraper.error_code = 0
            scraper.created_at = datetime.now()
            scraper.type = 1 #1: regular study; 2: pre-test

            scraper.query = query
            scraper.searchengine = searchengine
            scraper.study = study

            scrapers_.append(scraper)

    db.session.add_all(scrapers_)
    db.session.commit()

    flash('Result collection started. You will be notified via e-mail when all results have been collected.', 'success')
    return redirect(url_for("study", id=id))


@app.route('/study/<id>/run_pretest')
@login_required
def run_pretest(id):

    study = Study.query.get_or_404(id)

    study.status = 1
    study.updated_at = datetime.now()

    scrapers_ = []

    for query in study.queries[:5]:
        for searchengine in study.searchengines:
            scraper = Scraper()

            scraper.progress = 0
            scraper.counter = 0
            scraper.limit = study.result_count
            scraper.error_code = 0
            scraper.created_at = datetime.now()
            scraper.type = 2 #1: regular study; 2: pre-test

            scraper.query = query
            scraper.searchengine = searchengine
            scraper.study = study

    db.session.add_all(scrapers_)
    db.session.commit()

    flash('Pre-test started. You will be notified via e-mail when all results have been collected.', 'success')
    return redirect(url_for("study", id=id))
