"""
Query sampler module for the RAT application.

This module controls backend operations for seed keyword expansion workflows, 
including single-page setup wizards, geographical and linguistic configuration lookups, 
asynchronous multi-line text input filters combined with tabular CSV validation previews, 
progress tracking endpoints, and structured spreadsheet data generation pipelines.
"""

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

from io import BytesIO, StringIO
import csv
from sqlalchemy import desc

@app.route('/dashboard')
@login_required
def qs_studies():
    """
    Index view route displaying all current query sampler studies on the user dashboard.

    Args:
        None

    Returns:
        str: Rendered central dashboard view layout displaying linked studies.
    """
    user = User.query.get(current_user.id)
    
    rat_studies = user.studies
    qs_studies = user.qs_studies
    
    return render_template('dashboard.html', 
                           user=user, 
                           rat_studies=rat_studies, 
                           qs_studies=qs_studies)


@app.route('/query_sampler/download_template/<template_type>')
@login_required
def qs_download_template(template_type):
    """
    Generates and downloads a structural skeleton template CSV file for seed keyword uploads.

    Args:
        template_type (str): The configuration type key identifying the requested layout.

    Returns:
        Response: A Flask streaming file response providing the blank schema CSV file.
    """
    si = StringIO()
    cw = csv.writer(si)

    if template_type == 'queries': 
        header = ['query']
        cw.writerow(header)
        cw.writerow(['query1'])
        cw.writerow(['query2'])

    output_string = si.getvalue()
    si.close()
    encoded_output = output_string.encode('utf-8')

    return send_file(
        BytesIO(encoded_output),
        mimetype="text/csv; charset=utf-8",
        as_attachment=True,
        download_name=f"{template_type}_template.csv"
    )


@app.route('/query_sampler/preview_csv', methods=['POST'])
@login_required
def preview_qs_query_csv():
    """
    Validates an uploaded query CSV file and generates a JSON snapshot preview of its initial rows.

    Ensures that mandatory data headers are declared correctly and falls back 
    to alternative text encodings if reading via strict UTF-8 rules fails.

    Args:
        None

    Returns:
        Response: A Flask JSON string payload providing file content previews or validation failure errors.
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in the request.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'}), 400

    try:
        try:
            df = pd.read_csv(file, encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            df = pd.read_csv(file, encoding='latin-1')

        if 'query' not in df.columns:
            return jsonify({
                'success': False,
                'message': "Validation Error: The CSV must contain a column named 'query'."
            }), 400

        preview_data = df.head(10).fillna('').to_dict(orient='records')
        columns = df.columns.tolist()

        return jsonify({
            'success': True,
            'preview': preview_data,
            'columns': columns
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing file: {str(e)}'}), 500


@app.route('/query_sampler/new', methods=['GET', 'POST'])
@login_required
def new_qs_study_wizard():
    """
    Renders and processes the unified wizard to configure a new query sampler study.

    Parses geographical target regions, specific language identifiers, 
    and combines text-area manual inputs with uploaded batch files. It screens out 
    duplicate keyword strings before saving transaction contexts.

    Args:
        None

    Returns:
        Response: Forwarding routing instructions or the base wizard configuration interface.
    """
    form = QuerySamplerWizardForm()

    # Populate dropdown lists dynamically from reference databases
    form.geotargets.choices = [
        (g.criterion_id, g.name) for g in
        Qs_Geotarget.query.filter_by(target_type='Country').order_by(Qs_Geotarget.name).all()
    ]
    form.languages.choices = [
        (l.criterion_id, l.name) for l in
        Qs_Language_Code.query.order_by(Qs_Language_Code.name).all()
    ]

    if form.validate_on_submit():
        # 1. Gather keywords
        seed_keywords_text = form.seed_keywords.data
        
        # Split block input text strings into a sanitized array list
        final_keywords_list = [k.strip() for k in seed_keywords_text.splitlines() if k.strip()]

        # Verify additional file data drops (optional template parameter)
        uploaded_file = request.files.get(form.query_list.name)
        if uploaded_file and uploaded_file.filename != '':
            try:
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin-1')

                if 'query' in df.columns:
                    queries_from_file = df['query'].dropna().astype(str).tolist()
                    # Append external file keywords onto the active extraction list
                    final_keywords_list.extend([q.strip() for q in queries_from_file if q.strip()])
                else:
                    flash("Uploaded CSV is missing the required 'query' column.", "danger")
                    return render_template('query_sampler/new_qs_study_wizard.html', form=form, title="Create Query Sampler Study")
            except Exception as e:
                flash(f"Error processing the uploaded file: {e}", "danger")
                return render_template('query_sampler/new_qs_study_wizard.html', form=form, title="Create Query Sampler Study")

        # 2. Create a study database entity
        try:
            new_study = Qs_Study(
                name=form.name.data,
                description=form.description.data,
                created_at=datetime.utcnow(),
                status=0
            )
            
            user = User.query.get(current_user.id)
            if user:
                new_study.users.append(user)

            db.session.add(new_study)
            db.session.commit()

            # 3. Save unique keywords to database tables
            geotarget_id = form.geotargets.data
            language_id = form.languages.data
            
            # Filter structural duplicates using distinct sets
            unique_keywords = list(set(final_keywords_list))

            for keyword_text in unique_keywords:
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

        except Exception as e:
            db.session.rollback()
            flash(f"Database error: {str(e)}", "danger")

    return render_template('query_sampler/new_qs_study_wizard.html',
                           form=form,
                           title="Create Query Sampler Study")


@app.route('/query_sampler/new/create', methods=['POST'])
@login_required
def create_new_qs_study():
    """
    Constructs a basic query sampler study framework from raw fallback form variables.

    Args:
        None

    Returns:
        Response: Redirect instruction forward onto the setup presentation screen.
    """
    data_json_str = request.form.get('data')

    if not data_json_str:
        flash("Could not retrieve study data. Please try again.", "danger")
        return redirect(url_for('new_qs_study_wizard'))

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


@app.route('/query_sampler/show/<int:id>', methods=['GET'])
@login_required
def show_qs_study(id):
    """
    Renders the principal control dashboard showing metrics and logs for a single study.

    Compiles global tracking numbers, calculates macro execution percentages, 
    and checks if background worker tasks are actively running.

    Args:
        id (int): Unique primary key identifier of the selected Qs_Study database entry.

    Returns:
        str: Rendered study configuration view context.
    """
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
    total_keywords = Qs_Keyword.query.filter_by(qs_study_id=id).count()
    completed_keywords = Qs_Keyword.query.filter_by(qs_study_id=id, status=1).count()
    
    progress_percent = 0
    if total_keywords > 0:
        progress_percent = int((completed_keywords / total_keywords) * 100)
    
    is_busy = Qs_Keyword.query.filter(Qs_Keyword.qs_study_id == id, Qs_Keyword.status.in_([0, 2])).first() is not None
    status = not is_busy

    return render_template('query_sampler/show_qs_study.html',
                           title='Query Sampler Dashboard',
                           study=study,
                           keywords=keywords,
                           keyword_ideas_count=keyword_ideas_count,
                           status=status,
                           progress_percent=progress_percent,
                           total_keywords=total_keywords,
                           completed_keywords=completed_keywords)

@app.route('/query_sampler/export/<int:id>')
@login_required
def export_keyword_ideas(id):
    """
    Compiles all discovered expansion search keyword ideas into a flattened tabular matrix layout spreadsheet.

    Args:
        id (int): Unique primary key matching the selected source study.

    Returns:
        Response: A binary document download stream delivering the compiled Excel workbook report.
    """
    study = Qs_Study.query.get_or_404(id)
    results = db.session.query(
        Qs_Keyword_Idea,
        Qs_Keyword.keyword
    ).join(
        Qs_Keyword, Qs_Keyword_Idea.qs_keyword_id == Qs_Keyword.id
    ).filter(
        Qs_Keyword_Idea.qs_study_id == id
    ).order_by(
        Qs_Keyword.keyword.asc(),
        desc(Qs_Keyword_Idea.avg_monthly_searches)
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
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name='Keyword Ideas')
    output.seek(0)
    filename = f"{study.id}_{study.name.replace(' ', '_')}_keyword_ideas.xlsx"
    return send_file(output, download_name=filename, as_attachment=True)


@app.route('/query_sampler/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_qs_study(id):
    """
    Updates core study descriptive text fields or appends new keywords to an existing queue.

    Verifies user permissions before accepting incoming updates, automatically 
    re-using regional and language parameters configured on past data instances.

    Args:
        id (int): Unique primary identifier of the targeted active Qs_Study.

    Returns:
        str: Rendered update configuration dashboard window panel or custom dashboard forward rules.
    """
    study = Qs_Study.query.get_or_404(id)
    if study not in current_user.qs_studies:
        flash("You don't have permission to edit this study.", "danger")
        return redirect(url_for('qs_studies'))

    form = EditQsStudyForm()

    if form.validate_on_submit():
        study.name = form.name.data
        study.description = form.description.data
        new_keywords_str = form.new_keywords.data
        if new_keywords_str:
            first_keyword = Qs_Keyword.query.filter_by(qs_study_id=study.id).first()
            if first_keyword:
                geotarget_id = first_keyword.qs_geotarget_criterion_id
                language_id = first_keyword.qs_language_code_criterion_id
                
                new_keywords_list = [k.strip() for k in new_keywords_str.splitlines() if k.strip()]
                
                for keyword_text in new_keywords_list:
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
    Provides a real-time JSON polling API tracking quantitative keyword processing counters.

    Tracks absolute processing distributions across multiple distinct data execution parameters 
    and determines whether worker instances are occupied.

    Args:
        id (int): Unique primary key reference pointing to the logged Qs_Study record.

    Returns:
        Response: A Flask JSON dictionary containing live calculation metrics.
    """
    study = Qs_Study.query.get_or_404(id)
    if study not in current_user.qs_studies:
        return jsonify({'error': 'Permission denied'}), 403

    total_keywords = Qs_Keyword.query.filter_by(qs_study_id=id).count()
    completed_keywords = Qs_Keyword.query.filter_by(qs_study_id=id, status=1).count()
    processing_keywords = Qs_Keyword.query.filter_by(qs_study_id=id, status=2).count()

    progress_percent = 0
    if total_keywords > 0:
        progress_percent = int((completed_keywords / total_keywords) * 100)
        
    keyword_ideas_count = Qs_Keyword_Idea.query.filter_by(qs_study_id=id).count()
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
    Purges a query sampler study entity completely along with all cascading data records.

    Prompts for confirmation before executing deletions, cleaning keyword mappings 
    and dependent search results from relational database tables.

    Args:
        id (int): Unique primary key identifier of the target Qs_Study profile.

    Returns:
        str: Rendered verification template frame or standard main page forward directions.
    """
    form = ConfirmationForm()
    study = Qs_Study.query.get_or_404(id)
    if study not in current_user.qs_studies:
        flash("You don't have permission to delete this study.", "danger")
        return redirect(url_for('qs_studies'))

    if request.method == 'POST':
        try:
            # Purge downstream tables manually to handle execution contexts cleanly
            Qs_Keyword_Idea.query.filter_by(qs_study_id=id).delete()
            Qs_Keyword.query.filter_by(qs_study_id=id).delete()
            db.session.delete(study)
            db.session.commit()
            flash(f'Study "{study.name}" and all its data have been successfully deleted.', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting study {id}: {e}")
            flash(f'An error occurred while deleting the study. Please check the logs.', 'danger')
        
        return redirect(url_for('qs_studies'))

    return render_template('query_sampler/delete_qs_study_confirm.html',
                           study=study,
                           title="Confirm Deletion", form=form)