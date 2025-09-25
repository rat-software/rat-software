# VOLLSTÄNDIGER, KORRIGIERTER INHALT FÜR app/views/query_sampler.py

import os
import subprocess
import time
import json
from datetime import datetime
import pandas as pd
from flask import (render_template, request, redirect, flash,
                   url_for, current_app, send_file, jsonify)
from flask_security import login_required, current_user
from .. import app, db
from ..models import (Qs_Study, Qs_Keyword, Qs_Keyword_Idea,
                        Qs_Language_Code, Qs_Geotarget, User)
from ..forms import QuerySamplerWizardForm, ConfirmationForm, EditQsStudyForm

from io import BytesIO
from sqlalchemy import desc

# Index-Seite, die alle Query Sampler Studien auflistet




@app.route('/dashboard')
@login_required
def qs_studies():
    user = User.query.get(current_user.id)
    
    # Lade die regulären Studien (wie bisher)
    rat_studies = user.studies
    
    # NEU: Lade die Query Sampler Studien über die neue Relationship
    qs_studies = user.qs_studies
    
    return render_template('dashboard.html', 
                           user=user, 
                           rat_studies=rat_studies, 
                           qs_studies=qs_studies)

# Route für den mehrstufigen Wizard (behandelt GET und POST)
@app.route('/query_sampler/new_wizard', methods=['GET', 'POST'])
@login_required
def new_qs_study_wizard():
    form = QuerySamplerWizardForm()

    form.geotargets.choices = [
        (g.criterion_id, g.name) for g in
        Qs_Geotarget.query.filter_by(target_type='Country').order_by(Qs_Geotarget.name).all()
    ]
    form.languages.choices = [
        (l.criterion_id, l.name) for l in
        Qs_Language_Code.query.order_by(Qs_Language_Code.name).all()
    ]

    if form.validate_on_submit():
        form_data = {
            "name": form.name.data,
            "description": form.description.data,
            "geotargets": form.geotargets.data,
            "languages": form.languages.data,
            "seed_keywords": form.seed_keywords.data
        }
        
        # KORREKTUR: Suche nach criterion_id statt der primären ID
        geotarget = Qs_Geotarget.query.filter_by(criterion_id=form.geotargets.data).first()
        language = Qs_Language_Code.query.filter_by(criterion_id=form.languages.data).first()
        
        seed_keywords = [k.strip() for k in form.seed_keywords.data.splitlines() if k.strip()]
        
        confirm_form = ConfirmationForm()

        return render_template('query_sampler/confirm_new_qs_study.html',
                               form=form_data,
                               confirm=confirm_form,
                               geotarget=geotarget,
                               language=language,
                               seed_keywords=seed_keywords)

    return render_template('query_sampler/new_qs_study_wizard.html',
                           form=form,
                           title="Create Query Sampler Study")


# Route, die die Studie nach Bestätigung endgültig erstellt
@app.route('/query_sampler/new/create', methods=['POST'])
@login_required
def create_new_qs_study():
    data = dict(request.form)
    data_json_str = data["data"].replace("'", '"')
    dt = json.loads(data_json_str)

    new_study = Qs_Study(
        name=dt["name"],
        created_at=datetime.utcnow(),
        status=0
    )
    
    user = User.query.get(current_user.id)
    if user:
        new_study.users.append(user)

    db.session.add(new_study)
    db.session.commit()

    seed_keywords = [k.strip() for k in dt.get("seed_keywords", "").splitlines() if k.strip()]
    geotarget_id = dt.get("geotargets")
    language_id = dt.get("languages")

    for keyword_text in seed_keywords:
        new_keyword = Qs_Keyword(
            qs_study_id=new_study.id,
            qs_geotarget_criterion_id=int(geotarget_id),
            qs_language_code_criterion_id=int(language_id),
            keyword=keyword_text,
            created_at=datetime.utcnow(),
            status=0
        )
        db.session.add(new_keyword)

    db.session.commit()
    flash('Query Sampler study was successfully created!', 'success')
    return redirect(url_for('show_qs_study', id=new_study.id))


# Dashboard und Aktions-Routen
@app.route('/query_sampler/show/<int:id>', methods=['GET'])
@login_required
def show_qs_study(id):
    study = Qs_Study.query.get_or_404(id)
    keywords = db.session.query(
        Qs_Keyword.keyword,
        Qs_Language_Code.name.label('language'),
        Qs_Geotarget.name.label('region')
    ).join(
        Qs_Language_Code, Qs_Keyword.qs_language_code_criterion_id == Qs_Language_Code.criterion_id
    ).join(
        Qs_Geotarget, Qs_Keyword.qs_geotarget_criterion_id == Qs_Geotarget.criterion_id
    ).filter(Qs_Keyword.qs_study_id == id).all()
    
    keyword_ideas_count = Qs_Keyword_Idea.query.filter_by(qs_study_id=id).count()

    # --- NEUE LOGIK FÜR DEN FORTSCHRITT ---
    total_keywords = Qs_Keyword.query.filter_by(qs_study_id=id).count()
    completed_keywords = Qs_Keyword.query.filter_by(qs_study_id=id, status=1).count()
    
    progress_percent = 0
    if total_keywords > 0:
        progress_percent = int((completed_keywords / total_keywords) * 100)
    
    # Prüfen, ob noch Jobs laufen (Status 0 oder 2)
    is_busy = Qs_Keyword.query.filter(Qs_Keyword.qs_study_id == id, Qs_Keyword.status.in_([0, 2])).first() is not None
    status = not is_busy

    return render_template('query_sampler/show_qs_study.html',
                           title='Query Sampler Dashboard',
                           study=study,
                           keywords=keywords,
                           keyword_ideas_count=keyword_ideas_count,
                           status=status,
                           # Füge diese neuen Variablen für den initialen Ladevorgang hinzu
                           progress_percent=progress_percent,
                           total_keywords=total_keywords,
                           completed_keywords=completed_keywords)

@app.route('/query_sampler/export/<int:id>')
@login_required
def export_keyword_ideas(id):
    study = Qs_Study.query.get_or_404(id)

    # Query um die Sortieranweisung .order_by() erweitert
    results = db.session.query(
        Qs_Keyword_Idea,
        Qs_Keyword.keyword
    ).join(
        Qs_Keyword, Qs_Keyword_Idea.qs_keyword_id == Qs_Keyword.id
    ).filter(
        Qs_Keyword_Idea.qs_study_id == id
    ).order_by(
        Qs_Keyword.keyword.asc(),  # 1. Sortiere nach Seed Keyword (A-Z)
        desc(Qs_Keyword_Idea.avg_monthly_searches)  # 2. Dann nach Suchvolumen (absteigend)
    ).all()

    if not results:
        flash("No Keywords ideas found.", "warning")
        return redirect(url_for('show_qs_study', id=id))

    ideas_data = [
        {
            'Seed Keyword': seed_keyword,
            'Keyword Idea': idea.keyword_idea,
            'Monthly Searches (avg)': idea.avg_monthly_searches,
            'Competition': idea.competition
        }
        for idea, seed_keyword in results
    ]
    df = pd.DataFrame(ideas_data)

    # Der XLSX-Export-Teil bleibt unverändert
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name='Keyword Ideas')
    output.seek(0)
    filename = f"{study.id}_{study.name.replace(' ', '_')}_keyword_ideas.xlsx"
    return send_file(output, download_name=filename, as_attachment=True)


@app.route('/query_sampler/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_qs_study(id):
    """
    Ermöglicht das Bearbeiten des Namens, der Beschreibung
    und das Hinzufügen von Keywords zu einer Studie.
    """
    study = Qs_Study.query.get_or_404(id)
    if study not in current_user.qs_studies:
        flash("You don't have permission to edit this study.", "danger")
        return redirect(url_for('qs_studies'))

    form = EditQsStudyForm()

    if form.validate_on_submit():
        # 1. Studiendetails aktualisieren
        study.name = form.name.data
        study.description = form.description.data

        # 2. Neue Keywords hinzufügen
        new_keywords_str = form.new_keywords.data
        if new_keywords_str:
            # Targeting-Infos von einem bestehenden Keyword der Studie holen
            first_keyword = Qs_Keyword.query.filter_by(qs_study_id=study.id).first()
            if first_keyword:
                geotarget_id = first_keyword.qs_geotarget_criterion_id
                language_id = first_keyword.qs_language_code_criterion_id
                
                new_keywords_list = [k.strip() for k in new_keywords_str.splitlines() if k.strip()]
                
                for keyword_text in new_keywords_list:
                    # Duplikatprüfung: Keyword nicht erneut für diese Studie hinzufügen
                    exists = Qs_Keyword.query.filter_by(qs_study_id=study.id, keyword=keyword_text).first()
                    if not exists:
                        new_keyword = Qs_Keyword(
                            qs_study_id=study.id,
                            qs_geotarget_criterion_id=geotarget_id,
                            qs_language_code_criterion_id=language_id,
                            keyword=keyword_text,
                            created_at=datetime.utcnow(),
                            status=0
                        )
                        db.session.add(new_keyword)

        db.session.commit()
        flash('Study has been updated successfully!', 'success')
        return redirect(url_for('show_qs_study', id=study.id))

    # Für GET-Request: Formular mit existierenden Daten füllen
    form.name.data = study.name
    form.description.data = study.description

    existing_keywords = Qs_Keyword.query.filter_by(qs_study_id=study.id).order_by(Qs_Keyword.keyword).all()
    
    return render_template('query_sampler/edit_qs_study.html',
                           form=form,
                           study=study,
                           existing_keywords=existing_keywords,
                           title="Edit Study")

@app.route('/query_sampler/status/<int:id>')
@login_required
def qs_study_status(id):
    """
    API-Endpunkt, der den Fortschritt der Keyword-Generierung
    und die Anzahl der Ideen als JSON zurückgibt.
    """
    study = Qs_Study.query.get_or_404(id)
    if study not in current_user.qs_studies:
        return jsonify({'error': 'Permission denied'}), 403

    # Keyword-Status abfragen
    total_keywords = Qs_Keyword.query.filter_by(qs_study_id=id).count()
    completed_keywords = Qs_Keyword.query.filter_by(qs_study_id=id, status=1).count()
    processing_keywords = Qs_Keyword.query.filter_by(qs_study_id=id, status=2).count()

    progress_percent = 0
    if total_keywords > 0:
        progress_percent = int((completed_keywords / total_keywords) * 100)
        
    # Anzahl der Ideen abfragen
    keyword_ideas_count = Qs_Keyword_Idea.query.filter_by(qs_study_id=id).count()

    # Gesamtstatus (beschäftigt oder nicht)
    # Beschäftigt, wenn noch etwas verarbeitet wird (Status 2) oder noch nicht alles fertig ist.
    is_busy = processing_keywords > 0 or (completed_keywords < total_keywords)
    
    return jsonify({
        'progress_percent': progress_percent,
        'total_keywords': total_keywords,
        'completed_keywords': completed_keywords,
        'processing_keywords': processing_keywords,
        'keyword_ideas_count': keyword_ideas_count,
        'is_busy': is_busy
    })


@app.route('/query_sampler/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_qs_study(id):
    """
    Zeigt eine Bestätigungsseite (GET) und löscht eine Studie
    samt aller zugehörigen Daten (POST).
    """
    study = Qs_Study.query.get_or_404(id)
    if study not in current_user.qs_studies:
        flash("You don't have permission to delete this study.", "danger")
        return redirect(url_for('qs_studies'))

    if request.method == 'POST':
        try:
            # 1. Alle zugehörigen Keyword-Ideen löschen
            Qs_Keyword_Idea.query.filter_by(qs_study_id=id).delete()
            
            # 2. Alle zugehörigen Seed-Keywords löschen
            Qs_Keyword.query.filter_by(qs_study_id=id).delete()
            
            # 3. Die Studie selbst löschen
            db.session.delete(study)
            
            # 4. Transaktion bestätigen
            db.session.commit()
            
            flash(f'Study "{study.name}" and all its data have been successfully deleted.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting study {id}: {e}")
            flash(f'An error occurred while deleting the study. Please check the logs.', 'danger')
        
        return redirect(url_for('qs_studies'))

    # Bei GET-Request die Bestätigungsseite anzeigen
    return render_template('query_sampler/delete_qs_study_confirm.html',
                           study=study,
                           title="Confirm Deletion")