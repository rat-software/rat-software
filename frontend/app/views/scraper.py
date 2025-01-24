from .. import app, db
from ..models import Study, Scraper
from flask import Blueprint, render_template, flash, redirect, url_for
from flask_security import login_required, current_user
from datetime import datetime
#bp = Blueprint('scraper', __name__)

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
    # Retrieve the study based on the given ID or return a 404 error if not found
    study = Study.query.get_or_404(id)

    # Set the study status to 'running' and update the timestamp
    study.status = 1
    study.updated_at = datetime.now()

    # Initialize a list to hold scraper instances
    scrapers_ = []

    # Create a scraper for each combination of query and search engine
    for query in study.queries:
        for searchengine in study.searchengines:
            scraper = Scraper()
            scraper.progress = 0
            scraper.counter = 0
            scraper.limit = study.result_count
            scraper.error_code = 0
            scraper.created_at = datetime.now()
            scraper.type = 1  # 1: regular study; 2: pre-test

            # Associate the scraper with the current query, search engine, and study
            scraper.query_ = query
            scraper.searchengine = searchengine
            scraper.study = study

            # Add the scraper to the list
            scrapers_.append(scraper)

    # Add all new scrapers to the database session and commit the transaction
    db.session.add_all(scrapers_)
    db.session.commit()

    # Flash a success message and redirect to the study page
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
    # Retrieve the study based on the given ID or return a 404 error if not found
    study = Study.query.get_or_404(id)

    # Set the study status to 'running' and update the timestamp
    study.status = 1
    study.updated_at = datetime.now()

    # Initialize a list to hold scraper instances
    scrapers_ = []

    # Create a scraper for each combination of the first five queries and search engines
    for query in study.queries[:5]:
        for searchengine in study.searchengines:
            scraper = Scraper()
            scraper.progress = 0
            scraper.counter = 0
            scraper.limit = study.result_count
            scraper.error_code = 0
            scraper.created_at = datetime.now()
            scraper.type = 2  # 1: regular study; 2: pre-test

            # Associate the scraper with the current query, search engine, and study
            scraper.query_ = query
            scraper.searchengine = searchengine
            scraper.study = study

            # Add the scraper to the list
            scrapers_.append(scraper)

    # Add all new scrapers to the database session and commit the transaction
    db.session.add_all(scrapers_)
    db.session.commit()

    # Flash a success message and redirect to the study page
    flash('Pre-test started. You will be notified via e-mail when all results have been collected.', 'success')
    return redirect(url_for("study", id=id))
