from .. import app, db
from ..forms import ConfirmationForm
from ..models import Study, StudyURLFilter
from flask import render_template, flash, redirect, url_for, request
from flask_security import login_required

@app.route('/study/<id>/filters', methods=['GET', 'POST'])
@login_required
def url_filters(id):
    """
    Handles the display and update of URL include/exclude filters for a study.
    """
    study = Study.query.get_or_404(id)
    form = ConfirmationForm()

    if request.method == 'POST':
        # 1. Delete existing filters for this study
        StudyURLFilter.query.filter_by(study_id=id).delete()

        # 2. Read and save new “Include” URLs from the form
        include_urls_raw = request.form.get('include_urls', '')
        for url in include_urls_raw.splitlines():
            if url.strip(): # Nur nicht-leere Zeilen hinzufügen
                new_filter = StudyURLFilter(study_id=id, url=url.strip(), include=True, exclude=False)
                db.session.add(new_filter)

        # 3. Read and save new “Exclude” URLs from the form
        exclude_urls_raw = request.form.get('exclude_urls', '')
        for url in exclude_urls_raw.splitlines():
            if url.strip():
                new_filter = StudyURLFilter(study_id=id, url=url.strip(), include=False, exclude=True)
                db.session.add(new_filter)
        
        # 4. Commit all changes to the database
        db.session.commit()
        flash('URL filters have been updated successfully.', 'success')
        return redirect(url_for('study', id=id))

    # For GET requests, prepare the current filters to display in the form
    included_urls = [f.url for f in study.study_url_filters if f.include]
    excluded_urls = [f.url for f in study.study_url_filters if f.exclude]

    return render_template('studies/url_filters.html',
                           study=study,
                           form=form,
                           included_urls='\n'.join(included_urls),
                           excluded_urls='\n'.join(excluded_urls))