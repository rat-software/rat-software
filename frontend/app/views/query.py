from .. import app, db
from ..models import Study, Query
from flask import render_template, flash, redirect, url_for, request
from flask_security import login_required, current_user
from datetime import datetime


@app.route('/study/<id>/queries', methods=['GET', 'POST'])
@login_required
def queries(id):
    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Query).filter(Query.study_id == id).paginate(page, per_page=10)

    return render_template('studies/queries.html',
                           pagination=pagination,
                           id=id)
