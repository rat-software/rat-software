from .. import app, db
from ..models import Study, Query
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_security import login_required, current_user
from datetime import datetime
#bp = Blueprint('query', __name__)

from ..models import Result, Serp, Scraper, ResultAi, ResultChatbot

@app.route('/study/<id>/queries', methods=['GET', 'POST'])
@login_required
def queries(id):
    """
    Displays a paginated list of queries associated with a specific study.

    Args:
        id (int): The ID of the study whose queries are to be displayed.

    Returns:
        Renders the queries page with the paginated queries for the specified study.
    """
    # Get the current page number from the request arguments; default to 1 if not provided
    page = request.args.get('page', 1, type=int)    

    # Query the database for queries associated with the specified study ID
    # Paginate the results with 10 queries per page
    pagination = db.session.query(Query).filter(Query.study_id == id).order_by(Query.id.asc()).paginate(page=page, per_page=10)

    # Render the queries template with the paginated query results and study ID
    return render_template('studies/queries.html',
                           pagination=pagination,
                           id=id, study_id=id)

@app.route('/study/<id>/add_queries', methods=['POST'])
@login_required
def add_queries(id):
    """
    Parses a text area input and adds new queries to the study.
    Used primarily to feed the dynamic scrapers.
    """
    study = Study.query.get_or_404(id)
    new_keywords = request.form.get('new_keywords', '')
    
    # NEW: Get the limit from the form, default to 10 if missing
    query_limit = request.form.get('query_limit', 10, type=int)
    
    if new_keywords:
        keywords = [k.strip() for k in new_keywords.split('\n') if k.strip()]
        added_count = 0
        
        for kw in keywords:
            existing_query = db.session.query(Query).filter_by(study_id=id, query=kw).first()
            
            if not existing_query:
                new_q = Query(
                    query=kw, 
                    study_id=study.id, 
                    limit=query_limit,        # <--- UPDATED TO USE VARIABLE
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
    Safely deletes a query. Blocks deletion if any scraped results are already 
    associated with it or if it was imported via the browser extension.
    """
    query_obj = db.session.query(Query).get_or_404(query_id)
    study_id = query_obj.study_id
    
    # +++ NEW: Block extension queries from being deleted +++
    if query_obj.source_type == 'extension':
        flash('Keywords imported from the browser extension cannot be deleted.', 'danger')
        return redirect(url_for('queries', id=study_id))
    
    # 1. Check if any results exist for this query across all result types
    organic_count = db.session.query(Result).filter_by(query=query_obj.id).count()
    serp_count = db.session.query(Serp).filter_by(query=query_obj.id).count()
    ai_count = db.session.query(ResultAi).filter_by(query=query_obj.id).count()
    chatbot_count = db.session.query(ResultChatbot).filter_by(query=query_obj.id).count()
    
    total_results = organic_count + serp_count + ai_count + chatbot_count
    
    # 2. Prevent deletion if data has already been scraped
    if total_results > 0:
        flash('Cannot delete keyword: It already has scraped results associated with it.', 'danger')
    else:
        # 3. Safe to delete! First, remove any pending/orphan scraper jobs linked to this query
        db.session.query(Scraper).filter_by(query=query_obj.id).delete()
        
        # 4. Delete the actual query
        db.session.delete(query_obj)
        db.session.commit()
        flash(f'Keyword "{query_obj.query}" was deleted successfully.', 'success')
        
    return redirect(url_for('queries', id=study_id))