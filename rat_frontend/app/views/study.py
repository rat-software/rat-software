from .. import app, db
from ..forms import StudyForm, ConfirmationForm, StudySettingsForm, UploadResultsForm, ConfirmUploadForm
from ..models import (Study, Query, Answer,
                      Result, Classifier, RangeStudy, 
                      ResultAi, ResultAiSource, ResultSource, ResultChatbot, Serp)
from flask import Blueprint, render_template, flash, redirect, url_for, request, Response, send_file, jsonify
from markupsafe import Markup
from sqlalchemy.orm import raiseload, joinedload
from sqlalchemy import or_, and_, text, func
from flask_security import login_required, current_user, roles_accepted
from flask import send_file
from datetime import datetime
import pandas as pd
from io import BytesIO, StringIO
import json
import csv
import zipfile
import io
import os
import uuid
import base64
import html 
import re   
from werkzeug.utils import secure_filename
from urllib.parse import urlsplit, urlunsplit, parse_qs, urlencode

import requests
import urllib.parse
import time
import platform
import tempfile
import traceback

def upload_to_storage(file_data, filename):
    base_url = app.config.get('STORAGE_BASE_URL')
    
    if "127.0.0.1" in base_url or "localhost" in base_url:
        api_url = f"{base_url.rstrip('/')}/upload"
    else:
        if "/storage" not in base_url:
            api_url = f"{base_url.rstrip('/')}/storage/upload"
        else:
            api_url = f"{base_url.rstrip('/')}/upload"
            
    headers = {'X-API-Key': app.config.get('API_UPLOAD_KEY')}
    files = {'file': (filename, file_data, 'application/zip')}
    
    try:
        response = requests.post(api_url, headers=headers, files=files, timeout=10)
        if response.status_code == 200:
            return response.json().get('filename')
    except Exception as e:
        pass 
        
    try:
        if platform.system() == "Windows":
            local_storage_path = os.path.abspath(os.path.join(app.root_path, "..", "..", "storage", "sources"))
        else:
            local_storage_path = app.config.get('STORAGE_FOLDER')
            
        os.makedirs(local_storage_path, exist_ok=True)
        local_filepath = os.path.join(local_storage_path, filename)
        
        with open(local_filepath, "wb") as f:
            f.write(file_data)
        return filename
    except Exception as e:
        print(f"Local Storage fallback failed: {e}")
        return None

TRACKING_PARAMS_TO_REMOVE = [
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'gclid', 'dclid', 'fbclid', '_hsenc', '_hsmi', 'mkt_tok', 'msclkid',
    'mc_cid', 'mc_eid', 'trk', 'onwewe'
]

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'tmp_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def normalize_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip(): return ""
    try:
        parts = urlsplit(url)
        query_params = parse_qs(parts.query, keep_blank_values=True)
        filtered_params = {k: v for k, v in query_params.items() if k.lower() not in TRACKING_PARAMS_TO_REMOVE}
        new_query = urlencode(filtered_params, doseq=True)
        scheme = 'https'
        netloc = parts.netloc.lower()
        if netloc.startswith('www.'): netloc = netloc[4:]
        path = parts.path
        if path != '/' and path.endswith('/'): path = path[:-1]
        return urlunsplit((scheme, netloc, path, new_query, parts.fragment))
    except Exception: return url

def get_main_domain(url: str) -> str:
    if not isinstance(url, str) or not url.strip(): return ""
    try:
        parts = urlsplit(url)
        if parts.scheme and parts.netloc:
            return f"{parts.scheme}://{parts.netloc}/"
        return ""
    except Exception:
        return ""

def format_ai_text_to_html(text):
    if not text:
        return ""
    safe_text = html.escape(str(text))
    if '•' in safe_text:
        parts = safe_text.split('•')
        intro = parts[0].strip()
        intro = re.sub(r'\s{3,}', '<br><strong>', intro)
        if '<strong>' in intro: intro += '</strong>'
        list_html = "<ul>"
        for item in parts[1:]:
            clean_item = item.strip()
            clean_item = re.sub(r'\s{3,}', '</li></ul><br><strong>', clean_item)
            if '<strong>' in clean_item: clean_item += '</strong><ul><li>'
            list_html += f"<li>{clean_item}</li>"
        list_html += "</ul>"
        final_html = f"<p>{intro}</p>{list_html}"
        final_html = final_html.replace("<ul></ul>", "").replace("<strong></strong>", "")
        return final_html
    else:
        return f"<p>{safe_text.replace(chr(10), '<br>').replace(chr(13), '')}</p>"

def check_and_update_status(study):
    from sqlalchemy import or_, and_
    status_changed = False

    # 1. Echten, globalen Fortschritt berechnen (unabhängig von den Checkboxen!)
    total_tasks = db.session.query(ResultSource.result_id)\
        .join(Result, ResultSource.result_id == Result.id)\
        .filter(Result.study_id == study.id).count()
    
    finished_q = db.session.query(ResultSource.result_id)\
        .join(Result, ResultSource.result_id == Result.id)\
        .filter(Result.study_id == study.id)

    if study.assess_failed:
        finished_q = finished_q.filter(ResultSource.progress.in_([1, -1]))
    else:
        finished_q = finished_q.filter(
            or_(
                ResultSource.progress == 1, 
                and_(ResultSource.progress == -1, ResultSource.counter > 2)
            )
        )
    
    finished_tasks = finished_q.count()
    progress_percent = round((finished_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    ai_count = db.session.query(ResultAi.id).filter_by(study_id=study.id).count()
    chatbot_count = db.session.query(ResultChatbot.id).filter_by(study_id=study.id).count()
    serp_count = db.session.query(Serp.id).filter(Serp.study_id == study.id, Serp.file_path.isnot(None)).count()    
    has_data = (total_tasks > 0 or ai_count > 0 or chatbot_count > 0 or serp_count > 0)

    # 2. Status-Updates
    if study.status == 0 and has_data:
        study.status = 1
        status_changed = True

    if study.status in [0, 1, 3]:
        if total_tasks > 0 and finished_tasks >= total_tasks:
            study.status = 2
            progress_percent = 100
            status_changed = True
        elif total_tasks == 0 and has_data:
            study.status = 2
            progress_percent = 100
            status_changed = True

    if status_changed:
        db.session.commit()
        
    return study.status, progress_percent

def process_upload_file(study_id, filepath):
    study = Study.query.get(study_id)
    if not study: return False, "Study not found"

    try:
        is_zip = filepath.lower().endswith('.zip')
        df = None
        zip_ref = None

        if is_zip:
            if not zipfile.is_zipfile(filepath): return False, "Invalid ZIP file."
            zip_ref = zipfile.ZipFile(filepath, 'r')
            if 'rat_results.csv' not in zip_ref.namelist():
                zip_ref.close()
                return False, "rat_results.csv not found in ZIP"
            with zip_ref.open('rat_results.csv') as csvfile:
                df = pd.read_csv(csvfile)
        else:
            try: df = pd.read_csv(filepath)
            except: return False, "Invalid CSV file."

        if 'url' in df.columns and 'query' not in df.columns:
            df['query'] = 'Manual Import'
            df['engine'] = 'manual'
            df['country'] = 'xx'
            df['lang'] = 'xx'
            df['type'] = 'organic'
            df['rank'] = df.index + 1
            df['title'] = df['url']
            df['snippet'] = ''
            df['page'] = 1

        required_cols = ['query', 'engine', 'country', 'lang']
        if not all(col in df.columns for col in required_cols):
            if zip_ref: zip_ref.close()
            return False, f"Missing required columns in CSV. Needed: {required_cols}"

        query_cache = {}  
        serp_cache = {}   
        ai_parent_cache = {} 

        results_added = 0
        ai_added = 0
        ai_sources_added = 0

        for index, row in df.iterrows():
            img_fn = row['screenshot_file'] if 'screenshot_file' in df.columns and pd.notna(row['screenshot_file']) else None
            html_fn = row['html_file'] if 'html_file' in df.columns and pd.notna(row['html_file']) else None

            engine_str = f"{row['engine']}_{row['country']}_{row['lang']}".lower()
            
            query_text = row['query']
            if query_text not in query_cache:
                q = db.session.query(Query).filter_by(study_id=study.id, query=query_text).first()
                if not q:
                    q = Query(study_id=study.id, query=query_text, limit=10, created_at=datetime.now(), source_type='extension')
                    db.session.add(q)
                    db.session.flush()
                query_cache[query_text] = q.id
            query_id = query_cache[query_text]

            page_num = int(row['page']) if 'page' in row and pd.notna(row['page']) else 1
            serp_key = f"{query_id}_{engine_str}_{page_num}"

            if serp_key not in serp_cache:
                # 1. First, check whether there are any files (HTML/JPG) in the ZIP file
                has_content = False
                img_match = None
                html_match = None
                
                if zip_ref:
                    query_clean = re.sub(r'[^a-z0-9]', '', str(row['query']).lower())
                    engine_clean = re.sub(r'[^a-z0-9]', '', str(row['engine']).lower())
                    
                    if img_fn: 
                        img_fn_clean = str(img_fn).lower().replace('\\', '/')
                        img_match = next((f for f in zip_ref.namelist() if f.lower().replace('\\', '/').endswith(img_fn_clean)), None)
                        
                    if not img_match:
                        for f in zip_ref.namelist():
                            fl_clean = re.sub(r'[^a-z0-9]', '', f.lower())
                            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                                if (query_clean[:20] in fl_clean) and (engine_clean in fl_clean) and (f"p{page_num}j" in fl_clean or f"p{page_num}p" in fl_clean):
                                    img_match = f
                                    break
                                    
                    if html_fn:
                        html_fn_clean = str(html_fn).lower().replace('\\', '/')
                        html_match = next((f for f in zip_ref.namelist() if f.lower().replace('\\', '/').endswith(html_fn_clean)), None)
                        
                    if not html_match:
                        for f in zip_ref.namelist():
                            fl_clean = re.sub(r'[^a-z0-9]', '', f.lower())
                            if f.lower().endswith('.html'):
                                if (query_clean[:20] in fl_clean) and (engine_clean in fl_clean) and (f"p{page_num}h" in fl_clean):
                                    html_match = f
                                    break
                                
                    if img_match or html_match:
                        has_content = True

                # 2. ONLY if content is found do we create the SERP record
                if has_content:
                    serp = db.session.query(Serp).filter_by(study_id=study.id, query=query_id, page=page_num, engine_text=engine_str).first()
                    if not serp:
                        serp = Serp(study_id=study.id, query=query_id, page=page_num, created_at=datetime.now(), progress=0, engine_text=engine_str, result_type_text="serp")
                        db.session.add(serp)
                        db.session.flush()
                    
                    if not serp.file_path:
                        serp_zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(serp_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as sz:
                            if img_match: sz.writestr('screenshot.jpg', zip_ref.read(img_match))
                            if html_match: sz.writestr('source.html', zip_ref.read(html_match))
                        
                        serp_zip_buffer.seek(0)
                        remote_fn = upload_to_storage(serp_zip_buffer.read(), f"serp_{uuid.uuid4()}.zip")
                        if remote_fn:
                            serp.file_path = remote_fn
                            serp.progress = 1 
                        else:
                            flash(f"Screeenshot for SERP '{row['query']}' found, but could not be uploaded.", "danger")

                    db.session.flush()
                    serp_cache[serp_key] = serp.id
                else:
                    # No image/HTML found -> We will NOT generate a SERP listing!
                    serp_cache[serp_key] = None

            serp_id = serp_cache[serp_key]

            res_type = str(row['type']).lower().strip()
            
            if res_type == 'organic':
                url = row['url'] if pd.notna(row['url']) else ""
                title = row['title'] if pd.notna(row['title']) else ""
                snippet = row['snippet'] if pd.notna(row['snippet']) else ""
                rank = int(row['rank']) if pd.notna(row['rank']) else 0
                if url:
                    existing_res = db.session.query(Result).filter_by(study_id=study.id, query_id=query_id, position=rank, engine_text=engine_str).first()
                    if not existing_res:
                        norm_url = normalize_url(url)
                        new_res = Result(study_id=study.id, query_id=query_id, serp_id=serp_id, url=url, normalized_url=norm_url, title=title, description=snippet, position=rank, created_at=datetime.now(), imported=True, result_type_text=res_type, engine_text=engine_str)
                        db.session.add(new_res)
                        db.session.flush()
                        db.session.add(ResultSource(result_id=new_res.id, progress=0, counter=0))
                        results_added += 1

            elif 'ai' in res_type and 'overview' in res_type:
                ai_text = row['ai_full_text'] if pd.notna(row['ai_full_text']) else ""
                if not ai_text and pd.notna(row.get('snippet')): ai_text = row['snippet']
                if ai_text:
                    existing_ai = db.session.query(ResultAi).filter_by(study_id=study.id, query_id=query_id, engine_text=engine_str).first()
                    if not existing_ai:
                        formatted_html = format_ai_text_to_html(ai_text)
                        new_ai = ResultAi(study_id=study.id, query_id=query_id, answer=ai_text, answer_html=formatted_html, created_at=datetime.now(), result_type_text=res_type, engine_text=engine_str)
                        db.session.add(new_ai)
                        db.session.flush()
                        ai_parent_cache[f"{query_id}_{engine_str}"] = new_ai.id
                        ai_added += 1
                    else:
                        ai_parent_cache[f"{query_id}_{engine_str}"] = existing_ai.id

            elif 'ai' in res_type and 'source' in res_type:
                url = row['url'] if pd.notna(row['url']) else ""
                title = row['title'] if pd.notna(row['title']) else ""
                parent_ai_id = ai_parent_cache.get(f"{query_id}_{engine_str}")
                if url and parent_ai_id:
                    existing_src = db.session.query(ResultAiSource).filter_by(study_id=study.id, result_ai_id=parent_ai_id, url=url).first()
                    if not existing_src:
                        main_domain = get_main_domain(url)
                        new_ai_source = ResultAiSource(study_id=study.id, query_id=query_id, result_ai_id=parent_ai_id, url=url, title=title, main=main_domain, created_at=datetime.now(), progress=0, counter=0, result_type_text=res_type, engine_text=engine_str)
                        db.session.add(new_ai_source)
                        ai_sources_added += 1

        db.session.commit()
        if zip_ref: zip_ref.close()
        return True, f"Import complete: {results_added} organic, {ai_added} AI, {ai_sources_added} AI sources imported."
    except Exception as e:
        db.session.rollback()
        if zip_ref: zip_ref.close()
        traceback.print_exc()
        return False, f"Error during processing: {str(e)}"

# --- ROUTES ---

@app.route('/study/download_template/manual_results')
@login_required
def download_manual_template():
    si = StringIO()
    cw = csv.writer(si)
    header = ['query', 'engine', 'country', 'lang', 'page', 'type', 'rank', 'title', 'url', 'snippet', 'ai_full_text']
    cw.writerow(header)
    cw.writerow(['beispiel', 'google', 'de', 'de', '1', 'organic', '1', 'Titel', 'https://beispiel.de', 'Beschreibung...', ''])
    cw.writerow(['beispiel', 'google', 'de', 'de', '1', 'ai_overview', '', '', '', '', 'Der AI Text...'])
    output_string = si.getvalue()
    si.close()
    return Response(output_string.encode('utf-8'), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=rat_results_template.csv"})

@app.route('/study/download_template/<template_type>')
@login_required
def download_template(template_type):
    if template_type == 'manual_results': return download_manual_template()
    si = StringIO()
    cw = csv.writer(si)
    if template_type == 'urls': cw.writerow(['url'])
    elif template_type == 'queries': cw.writerow(['query'])
    output_string = si.getvalue()
    si.close()
    return Response(output_string.encode('utf-8'), mimetype="text/csv", headers={"Content-disposition": f"attachment; filename={template_type}_template.csv"})

@app.route('/study/<id>/upload_results', methods=['POST'])
@login_required
def upload_study_results(id):
    study = Study.query.get_or_404(id)
    form = UploadResultsForm()
    if form.validate_on_submit():
        file = form.results_file.data
        if file:
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            try:
                df = None
                if filename.lower().endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as z:
                        if 'rat_results.csv' in z.namelist():
                            with z.open('rat_results.csv') as f:
                                df = pd.read_csv(f)
                else:
                    df = pd.read_csv(file_path)
                
                if df is not None:
                    if 'url' in df.columns and 'query' not in df.columns:
                        df['type'] = 'organic'
                        df['rank'] = df.index + 1
                    
                    preview_rows = []
                    if 'type' in df.columns:
                        organic_df = df[df['type'].astype(str).str.lower() == 'organic'].head(5)
                        preview_rows.extend(organic_df.to_dict(orient='records'))
                        
                        ai_df = df[df['type'].astype(str).str.contains('ai_overview', case=False, na=False)].head(3)
                        preview_rows.extend(ai_df.to_dict(orient='records'))

                        ai_sources_df = df[df['type'].astype(str).str.contains('ai_source', case=False, na=False)].head(3)
                        preview_rows.extend(ai_sources_df.to_dict(orient='records'))
                    else:
                        preview_rows = df.head(10).to_dict(orient='records')

                    row_count = len(df)
                    columns = df.columns.tolist()
                    confirm_form = ConfirmUploadForm()
                    confirm_form.filename.data = filename
                    return render_template('studies/preview_import.html', study=study, preview_rows=preview_rows, columns=columns, row_count=row_count, confirm_form=confirm_form)
                else:
                    flash('CSV could not be read.', 'danger')
            except Exception as e:
                flash(f'Error while processing file: {str(e)}', 'danger')
    return redirect(url_for('study', id=id))

@app.route('/study/<id>/confirm_upload', methods=['POST'])
@login_required
def confirm_study_upload(id):
    study = Study.query.get_or_404(id)
    form = ConfirmUploadForm()
    if form.validate_on_submit():
        filename = form.filename.data
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            success, message = process_upload_file(id, file_path)
            try: os.remove(file_path)
            except: pass
            if success:
                check_and_update_status(study)
                flash(message, 'success')
            else:
                flash(f'Import failed: {message}', 'danger')
        else:
            flash('Session expired. Please upload again.', 'warning')
    return redirect(url_for('study', id=id))

@app.route('/study/preview_csv', methods=['POST'])
@login_required
def preview_csv():
    if 'file' not in request.files: return jsonify({'success': False}), 400
    return jsonify({'success': True}) 

@app.route('/study/<int:id>/progress')
@login_required
def study_progress(id):
    study = Study.query.get_or_404(id)
    status, progress_percent = check_and_update_status(study)
    
    return jsonify({
        'status': status, 
        'progress_percent': progress_percent,
        'results': db.session.query(Result).filter(Result.study_id == id).count(),
        'results_ai': db.session.query(ResultAi).where(ResultAi.study_id == id).count(),
        'results_chatbot': db.session.query(ResultChatbot).where(ResultChatbot.study_id == id).count(),
        'results_serp': db.session.query(Serp).filter(Serp.study_id == id, Serp.file_path.isnot(None)).count(),        
        'ai_source_count': db.session.query(ResultAiSource.id).filter(ResultAiSource.study_id == id).count()
    })

@app.route('/studies', methods=['GET', 'POST'])
@login_required
@roles_accepted('Admin')
def studies():
    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Study).order_by(Study.id.desc()).paginate(page, per_page=10)
    return render_template('studies/studies.html', pagination=pagination)

@app.route('/study/<id>', methods=['GET'])
@login_required
def study(id):
    study = Study.query.get_or_404(id)
    status, progress_percent = check_and_update_status(study)
    
    results = db.session.query(Result).filter(Result.study_id == id).count()
    results_ai = db.session.query(ResultAi).where(ResultAi.study_id == id).count()
    results_chatbot = db.session.query(ResultChatbot).where(ResultChatbot.study_id == id).count()
    results_serp = db.session.query(Serp).filter(Serp.study_id == id, Serp.file_path.isnot(None)).count()    
    ai_source_count = db.session.query(ResultAiSource.id).filter(ResultAiSource.study_id == id).count()

    recent_queries = db.session.query(Query).filter_by(study_id=id).order_by(Query.id.asc()).limit(5).all()
    total_queries = db.session.query(Query).filter_by(study_id=id).count()

    engine_rows = db.session.query(Serp.engine_text).filter(Serp.study_id == id, Serp.engine_text.isnot(None)).distinct().all()
    imported_engines = []
    for row in engine_rows:
        parts = row[0].split('_')
        if len(parts) >= 3:
            imported_engines.append(f"{parts[0].capitalize()} ({parts[1].upper()} / {parts[2].upper()})")
        else:
            imported_engines.append(row[0].replace('_', ' ').title())


    answers = Answer.query.filter(Answer.study == study, Answer.status != 0).count()
    max_answers = Answer.query.filter(Answer.study == study).count()
    a_pct = round(answers / max_answers * 100) if max_answers != 0 else 0

    upload_form = UploadResultsForm()
    settings_form = StudySettingsForm(obj=study)
    
    available_types = set()
    for model in [Result, ResultAi, ResultChatbot, Serp]:
        for r in db.session.query(model.result_type_text).filter_by(study_id=id).distinct():
            if r[0] and r[0] != 'ai_source': 
                available_types.add(r[0])
    if db.session.query(Serp.id).filter_by(study_id=id).first(): 
        available_types.add('serp')

    type_labels = {
        'serp': 'SERP (Search Engine Result Page)',
        'organic': 'Organic Results (Standard Links)',
        'ai_overview': 'AI Overview (Generative AI Answer)',
        'chatbot': 'Chatbot Answer'
    }

    settings_form.classifiers.choices = [(c.id, c.display_name) for c in Classifier.query.filter_by(display=True).all()]
    settings_form.assessment_result_types.choices = [
        (t, type_labels.get(t, t.replace('_', ' ').title())) 
        for t in sorted(list(available_types))
    ]
    settings_form.classifiers.data = [c.id for c in study.classifier]
    
    if study.assessable_result_types_text:
        settings_form.assessment_result_types.data = study.assessable_result_types_text.split(',')

    existing_ranges = RangeStudy.query.filter_by(study=study.id).all()
    if not request.form:
        while len(settings_form.ranges) > 0: settings_form.ranges.pop_entry()
        for r in existing_ranges: 
            settings_form.ranges.append_entry(data={'start_range': r.range_start, 'end_range': r.range_end})

    return render_template('studies/study.html', study=study, 
                           progress_percent=progress_percent, # Verhindert das 0% Flackern beim Laden
                           results=results, results_ai=results_ai, ai_source_count=ai_source_count, 
                           results_chatbot=results_chatbot, results_serp=results_serp,
                           recent_queries=recent_queries, total_queries=total_queries, imported_engines=imported_engines,
                           answers=answers, max_answers=max_answers, a_pct=a_pct, 
                           upload_form=upload_form, settings_form=settings_form, base=request.url_root)

@app.route('/study/<id>/update_settings', methods=['POST'])
@login_required
def update_study_settings(id):
    study = Study.query.get_or_404(id)
    form = StudySettingsForm(request.form)
    
    available_types = set()
    for model in [Result, ResultAi, ResultChatbot, Serp]:
        for r in db.session.query(model.result_type_text).filter_by(study_id=id).distinct():
            if r[0] and r[0] != 'ai_source': 
                available_types.add(r[0])
    if db.session.query(Serp.id).filter_by(study_id=id).first(): 
        available_types.add('serp')
            
    type_labels = {
        'serp': 'SERP (Search Engine Result Page)',
        'organic': 'Organic Results (Standard Links)',
        'ai_overview': 'AI Overview (Generative AI Answer)',
        'chatbot': 'Chatbot Answer'
    }

    form.classifiers.choices = [(c.id, c.display_name) for c in Classifier.query.filter_by(display=True).all()]
    form.assessment_result_types.choices = [
        (t, type_labels.get(t, t.replace('_', ' ').title())) 
        for t in sorted(list(available_types))
    ]

    if form.validate_on_submit():
        study.assessable_result_types_text = ",".join(form.assessment_result_types.data) if form.assessment_result_types.data else ""
        
        # --- 1. SAVE LIVE MODE ---
        study.live_link_mode = form.live_link_mode.data
        
        # ---  2. SHOW URLS LOGIC ---
        if study.live_link_mode:
            study.show_urls = True  
        else:
            study.show_urls = form.show_urls.data 
            
        study.task = request.form.get('task_description', '')
        study.show_ai_sources = form.show_ai_sources.data
        study.assess_failed = form.assess_failed.data

        study.limit_per_participant = form.limit_per_participant.data
        study.max_results_per_participant = form.max_results_per_participant.data if form.limit_per_participant.data else None
        study.classifier = [Classifier.query.get(cid) for cid in form.classifiers.data]
        
        RangeStudy.query.filter_by(study=study.id).delete()
        for r_data in form.ranges.data:
            if r_data['start_range'] and r_data['end_range']:
                db.session.add(RangeStudy(study=study.id, range_start=r_data['start_range'], range_end=r_data['end_range']))
        
        study.updated_at = datetime.now()
        db.session.commit()
        
        check_and_update_status(study)
        
        flash('Configuration saved.', 'success')
    else: 
        flash('There was an error with saving the configuration.', 'danger')
    return redirect(url_for('study', id=id))

@app.route('/study/new', methods=['GET'])
@login_required
def new_study():
    form = StudyForm()
    return render_template('studies/new_study.html', form=form, title="Create new study")

@app.route('/study/new/create/', methods=['POST'])
@login_required
def create_new_study():
    name = request.form.get("name")
    description = request.form.get("description")
    study_id_raw = request.form.get("id", "0")
    try: study_id = int(study_id_raw)
    except: study_id = 0

    if study_id == 0:
        study = Study(name=name, description=description, status=0, created_at=datetime.now(), result_count=10)
        study.users.append(current_user)
        db.session.add(study)
        db.session.commit()
        flash('Study created.', 'success')
        return redirect(url_for('study', id=study.id))
    else:
        study = Study.query.get_or_404(study_id)
        study.name = name
        study.description = description
        study.updated_at = datetime.now()
        db.session.commit()
        flash('Study updated.', 'success')
        return redirect(url_for('study', id=study.id))

@app.route('/study/<id>/edit', methods=['GET'])
@login_required
def edit_study(id):
    study = Study.query.get_or_404(id)
    form = StudyForm(obj=study)
    form.id.data = study.id
    return render_template('studies/new_study.html', form=form, study=study, title=f"Edit study: {study.name}")

@app.route('/study/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete_study(id):
    study = Study.query.get_or_404(id)
    form = ConfirmationForm()
    
    if form.validate_on_submit():
        try:
            files_to_delete = []
            serps = Serp.query.filter_by(study_id=study.id).all()
            for serp in serps:
                if serp.file_path: files_to_delete.append(serp.file_path)
                    
            results = Result.query.filter_by(study_id=study.id).all()
            for res in results:
                for source in res.sources:
                    if source and source.file_path: files_to_delete.append(source.file_path)

            db.session.execute(text("DELETE FROM result_source WHERE result IN (SELECT id FROM result WHERE study = :sid)"), {'sid': study.id})
            db.session.delete(study)
            db.session.commit()
            
            storage_dir = app.config.get('STORAGE_FOLDER')
            deleted_count = 0
            for filename in set(files_to_delete): 
                file_path = os.path.join(storage_dir, filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except: pass

            flash(f'Study deleted. {deleted_count} files removed.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            
    return render_template('studies/delete_study.html', form=form, study=study)

@app.route('/study/<id>/close')
@login_required
def close_study(id):
    study = Study.query.get_or_404(id)
    study.status = 4 # Geschlossen
    db.session.commit()
    flash('Study archived.', 'success')
    return redirect(url_for("study", id=id))


@app.route('/study/download_extension')
@login_required
def download_extension():
    # 1. Define the path for the log file (e.g., in the app's main directory)
    log_file_path = os.path.join(app.root_path, 'extension_downloads.csv')
    
    # 2. Check whether the file already exists so that a header can be written if necessary
    file_exists = os.path.isfile(log_file_path)
    
    # 3. Append data to the CSV file
    with open(log_file_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Timestamp', 'User_ID', 'User_Email']) # CSV Header
        
        # Write a data record for this download
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            current_user.id,
            current_user.email
        ])

    # 4. Send the actual ZIP file to the user
    extension_path = os.path.join(app.root_path, 'static', 'rat-extension_v1.zip')
    return send_file(extension_path, as_attachment=True)