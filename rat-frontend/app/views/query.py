"""
Query management module for the RAT application.

This module controls backend operations for processing keyword targets, including 
paginated listings, multi-line batch inserts with customizable retrieval depth limits, 
and safe deletion validations that prevent the removal of active research data.
"""

from .. import app, db
from ..models import Study, Query
from flask import render_template, flash, redirect, url_for, request
from flask_security import login_required
from datetime import datetime
from ..models import Result, Serp, Scraper, ResultAi, ResultChatbot

@app.route('/study/<id>/queries', methods=['GET', 'POST'])
@login_required
def queries(id):
    """
    Displays a paginated list of queries associated with a specific study.

    Queries the database for tracking keys matching the designated study ID 
    and partitions the dashboard output into sequential index blocks.

    Args:
        id (int): The unique primary key identifier of the targeted Study.

    Returns:
        str: The rendered HTML workspace displaying the paginated study keywords.
    """
    # Fetch the target page number from request args; default to index page 1
    page = request.args.get('page', 1, type=int)    

    # Extract matching search keywords partitioned by a fixed ceiling of 10 items per view
    pagination = db.session.query(Query).filter(Query.study_id == id).order_by(Query.id.asc()).paginate(page=page, per_page=10)

    return render_template('studies/queries.html',
                           pagination=pagination,
                           id=id, study_id=id)

@app.route('/study/<id>/add_queries', methods=['POST'])
@login_required
def add_queries(id):
    """
    Parses newline-separated text inputs and registers new keywords to a study.

    Extracts multi-line form data inputs, filters out duplicates, applies 
    customized search result depth caps, and updates transaction states 
    to feed the automated network scraper queues.

    Args:
        id (str or int): The unique identifier of the active Study instance.

    Returns:
        Response: A redirect back onto the parent study configuration console.
    """
    study = Study.query.get_or_404(id)
    new_keywords = request.form.get('new_keywords', '')
    
    # Retrieve the retrieval depth boundary from the input form; default to 10 if missing
    query_limit = request.form.get('query_limit', 10, type=int)
    
    if new_keywords:
        keywords = [k.strip() for k in new_keywords.split('\n') if k.strip()]
        added_count = 0
        
        for kw in keywords:
            # Check for existing records to prevent unique constraint conflicts
            existing_query = db.session.query(Query).filter_by(study_id=id, query=kw).first()
            
            if not existing_query:
                new_q = Query(
                    query=kw, 
                    study_id=study.id, 
                    limit=query_limit,        # Configured retrieval threshold per keyword target
                    created_at=db.func.now(),
                    source_type='manual'
                )
                db.session.add(new_q)
                added_count += 1
        
        db.session.commit()
        
        if added_count > 0:
            flash(f'Successfully added {added_count} new keywords with a limit of {query_limit} results each.', 'success')
        else:
            flash('No new keywords added. They might already exist in this study.', 'info')
    else:
        flash('No keywords were provided.', 'warning')
        
    return redirect(url_for('study', id=id))


@app.route('/query/<int:query_id>/delete', methods=['POST'])
@login_required
def delete_query(query_id):
    """
    Safely deletes a query from the database repository.

    Evaluates structural associations across all core data tables. The removal process 
    is intentionally blocked if the target keyword possesses scraped dataset records 
    or originated from a client browser extension import.

    Args:
        query_id (int): The unique primary key matching the targeted Query record.

    Returns:
        Response: A redirect back onto the paginated keywords overview workspace.
    """
    query_obj = db.session.query(Query).get_or_404(query_id)
    study_id = query_obj.study_id
    
    # Restrict deletions if protected by external browser integration rules
    if query_obj.source_type == 'extension':
        flash('Keywords imported from the browser extension cannot be deleted.', 'danger')
        return redirect(url_for('queries', id=study_id))
    
    # 1. Count associated records across all available search media layers
    organic_count = db.session.query(Result).filter_by(query=query_obj.id).count()
    serp_count = db.session.query(Serp).filter_by(query=query_obj.id).count()
    ai_count = db.session.query(ResultAi).filter_by(query_id=query_obj.id).count()
    chatbot_count = db.session.query(ResultChatbot).filter_by(query_id=query_obj.id).count()
    
    total_results = organic_count + serp_count + ai_count + chatbot_count
    
    # 2. Block the action if dependent historical entries rely on this reference key
    if total_results > 0:
        flash('Cannot delete keyword: It already has scraped results associated with it.', 'danger')
    else:
        # 3. Safe termination path: Purge any pending scraper worker requests linked to this item
        db.session.query(Scraper).filter_by(query=query_obj.id).delete()
        
        # 4. Remove the core query entity record from transaction contexts
        db.session.delete(query_obj)
        db.session.commit()
        flash(f'Keyword "{query_obj.query}" was deleted successfully.', 'success')
        
    return redirect(url_for('queries', id=study_id))