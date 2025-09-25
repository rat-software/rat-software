from .. import app, db
from ..models import Study, Scraper
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_security import login_required, current_user
from datetime import datetime

@app.route('/study/<id>/run')
@login_required
def run_study(id):
    """
    Starts the process of collecting results for a specific study by creating scrapers
    for each search engine and query associated with the study. Updates the study's status
    to 'running' and notifies the user that result collection has started.

    Args:
        id (int): The ID of the study to be processed.

    Returns:
        Redirects to the study page with a success message.
    """
    study = Study.query.get_or_404(id)
    study.status = 1
    study.updated_at = datetime.now()
    scrapers_ = []

    for query in study.queries:
        for searchengine in study.searchengines:
            scraper = Scraper()
            scraper.progress = 0
            scraper.counter = 0
            scraper.limit = study.result_count
            scraper.error_code = 0
            scraper.created_at = datetime.now()
            scraper.type = 1  # 1: regular study; 2: pre-test

            # NEU: Setzt den Ergebnistyp des Scrapers basierend auf der Suchmaschine.
            # Annahme: Das Feld heißt 'resulttype_id' im SearchEngine-Modell.
            # Bitte passen Sie es an, falls es z.B. nur 'resulttype' heißt.
            scraper.resulttype = searchengine.resulttype

            scraper.query_ = query
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
    """
    Starts a pre-test process for a specific study by creating scrapers
    for the first five queries and each search engine associated with the study.
    Updates the study's status to 'running' and notifies the user that the pre-test has started.

    Args:
        id (int): The ID of the study to be processed.

    Returns:
        Redirects to the study page with a success message.
    """
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
            scraper.type = 2  # 1: regular study; 2: pre-test

            # NEU: Setzt den Ergebnistyp des Scrapers basierend auf der Suchmaschine.
            # Annahme: Das Feld heißt 'resulttype_id' im SearchEngine-Modell.
            # Bitte passen Sie es an, falls es z.B. nur 'resulttype' heißt.
            scraper.resulttype = searchengine.resulttype

            scraper.query_ = query
            scraper.searchengine = searchengine
            scraper.study = study
            scrapers_.append(scraper)

    db.session.add_all(scrapers_)
    db.session.commit()

    flash('Pre-test started. You will be notified via e-mail when all results have been collected.', 'success')
    return redirect(url_for("study", id=id))