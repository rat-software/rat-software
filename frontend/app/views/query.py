from .. import app, db
from ..models import Study, Query
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_security import login_required, current_user
from datetime import datetime
#bp = Blueprint('query', __name__)

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
                           id=id)
