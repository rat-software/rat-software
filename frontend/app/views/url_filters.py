from .. import app, db
from ..forms import ConfirmationForm # Wiederverwendung für einfache Formulare
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
    form = ConfirmationForm() # Wir verwenden ein einfaches Formular nur für den CSRF-Schutz

    if request.method == 'POST':
        # 1. Bestehende Filter für diese Studie löschen
        StudyURLFilter.query.filter_by(study_id=id).delete()

        # 2. Neue "Include"-URLs aus dem Formular auslesen und speichern
        include_urls_raw = request.form.get('include_urls', '')
        for url in include_urls_raw.splitlines():
            if url.strip(): # Nur nicht-leere Zeilen hinzufügen
                new_filter = StudyURLFilter(study_id=id, url=url.strip(), include=True, exclude=False)
                db.session.add(new_filter)

        # 3. Neue "Exclude"-URLs aus dem Formular auslesen und speichern
        exclude_urls_raw = request.form.get('exclude_urls', '')
        for url in exclude_urls_raw.splitlines():
            if url.strip(): # Nur nicht-leere Zeilen hinzufügen
                new_filter = StudyURLFilter(study_id=id, url=url.strip(), include=False, exclude=True)
                db.session.add(new_filter)
        
        # 4. Änderungen in der Datenbank speichern und zum Dashboard zurückkehren
        db.session.commit()
        flash('URL filters have been updated successfully.', 'success')
        return redirect(url_for('study', id=id))

    # Bei GET-Request: Bestehende Filter laden und das Template rendern
    included_urls = [f.url for f in study.study_url_filters if f.include]
    excluded_urls = [f.url for f in study.study_url_filters if f.exclude]

    return render_template('studies/url_filters.html',
                           study=study,
                           form=form,
                           included_urls='\n'.join(included_urls),
                           excluded_urls='\n'.join(excluded_urls))