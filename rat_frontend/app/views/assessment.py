from .. import app, db, csrf
from ..models import Study, Participant, Answer, Question, Result, StudyURLFilter, ResultAi, ResultChatbot, Source, ResultSource, Serp, RangeStudy
from flask import render_template, flash, redirect, url_for, request
from flask_login import logout_user
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_, and_
from flask_wtf import FlaskForm
from urllib.parse import urlparse

from flask import current_app

import os
import zipfile
import io
from flask import send_file

from werkzeug.utils import secure_filename
from itsdangerous import URLSafeTimedSerializer, BadSignature

def get_signed_storage_url(file_path, file_type='screenshot'):
    api_key = current_app.config.get('API_UPLOAD_KEY')
    base_url = current_app.config.get('API_URL')
    
    serializer = URLSafeTimedSerializer(api_key)
    ticket = serializer.dumps({'filename': file_path}, salt='source-view')
    
    return f"{base_url}/view/{file_path}/{file_type}?ticket={ticket}"

def clean_filter_string(url_filter: str) -> str:
    try:
        if '://' not in url_filter:
            url_filter = 'http://' + url_filter
        netloc = urlparse(url_filter).netloc.lower()
        if netloc.startswith('www.'):
            return netloc[4:]
        return netloc
    except:
        return url_filter.lower()

@app.context_processor
def inject_storage_urls():
    return dict(get_storage_url=get_signed_storage_url)

@app.route('/study/<study_id>/assessments/<participant_id>', methods=["GET", "POST"])
def assessments(study_id, participant_id):
    logout_user()
    study = Study.query.get_or_404(study_id)
    participant = Participant.query.get_or_404(participant_id)

    query = db.session.query(Answer).filter(
        Answer.participant == participant,
        Answer.study == study
    )
    
    questions_count = len(study.questions)
    
    if questions_count > 0:
        all_tasks_count = query.count() // questions_count
        closed_tasks_count = query.filter(Answer.status == 1).count() // questions_count
        skipped_tasks_count = query.filter(Answer.status == 2).count() // questions_count
    else:
        all_tasks_count = 0
        closed_tasks_count = 0
        skipped_tasks_count = 0

    if all_tasks_count > 0:
        pct = round((closed_tasks_count + skipped_tasks_count) / all_tasks_count * 100)
    else:
        pct = 0

    answer = query.filter(Answer.status == 0).first()

    if answer:
        task_type = answer.result_type_text.replace('_', ' ').title() if answer.result_type_text else 'Unknown'

        task_item = None
        if answer.result_id:
            task_item = answer.result
        elif answer.result_ai_id:
            task_item = answer.result_ai
        elif answer.result_chatbot_id:
            task_item = answer.result_chatbot
        elif answer.result_serp_id:
            task_item = answer.result_serp
            
        if not task_item:
            flash('Error loading task item.', 'danger')
            return redirect(url_for('participant', id=participant_id))
            
        answers_for_item = []
        if answer.result_id:
            answers_for_item = query.filter(Answer.result_id == task_item.id).all()
        elif answer.result_ai_id:
            answers_for_item = query.filter(Answer.result_ai_id == task_item.id).all()
        elif answer.result_chatbot_id:
            answers_for_item = query.filter(Answer.result_chatbot_id == task_item.id).all()
        elif answer.result_serp_id:
            answers_for_item = query.filter(Answer.result_serp_id == task_item.id).all()

        form = FlaskForm()

        if request.method == 'POST':
            errors = {}
            for ans in answers_for_item:
                field_name = f'question_{ans.question.id}'
                
                if ans.question.questiontype.display == 'checkbox':
                    selected_options = request.form.getlist(field_name)
                    if not selected_options:
                        errors[ans.question.id] = 'Please select at least one option.'
                    else:
                        ans.value = ','.join(selected_options)
                        ans.status = 1
                else:
                    ans.value = request.form.get(field_name)
                    if not ans.value and ans.question.questiontype.display != 'info':
                        errors[ans.question.id] = 'This field is required.'
                    else:
                        ans.status = 1

            if not errors:
                db.session.commit()
                next_answer = query.filter(Answer.status == 0).first()
                if next_answer:
                    return redirect(url_for('assessments', study_id=study.id, participant_id=participant.id))
                else:
                    return redirect(url_for('participant', id=participant.id))

            return render_template('assessments/assessment.html',
                                   form=form, answers=answers_for_item, task_item=task_item, task_type=task_type,
                                   all=all_tasks_count, closed=closed_tasks_count, pct=pct,
                                   show_urls=study.show_urls, study=study, errors=errors, submitted_data=request.form)

        return render_template('assessments/assessment.html', form=form, answers=answers_for_item,
                               task_item=task_item, task_type=task_type, all=all_tasks_count,
                               closed=closed_tasks_count, pct=pct, show_urls=study.show_urls,
                               study=study, errors={}, submitted_data={})

    else:
        flash('Assessment completed!', 'success')
        return redirect(url_for('participant', id=participant.id))

@app.route('/assessment/<participant_id>/<study_id>', methods=["GET", "POST"])
def assessment(participant_id, study_id):
    logout_user()
    participant = Participant.query.get_or_404(participant_id)
    study = Study.query.get_or_404(study_id)
    db.session.expire_all()

    open_res_q = db.session.query(Answer.result_id).filter(
        Answer.participant_id == participant.id,
        Answer.study_id == study.id,
        Answer.status == 0,
        Answer.result_id.isnot(None)
    ).join(Result).join(Result.source_associations)
    
    if study.assess_failed:
        open_res_q = open_res_q.filter(or_(ResultSource.progress == 1, ResultSource.progress == -1))
    else:
        open_res_q = open_res_q.filter(ResultSource.progress == 1)
        
    open_result_tasks_query = open_res_q.filter(
        Result.normalized_url.isnot(None),
        Result.normalized_url != ""
    )

    # --- RANGE FILTER WIEDER DA ---
    ranges = RangeStudy.query.filter_by(study=study.id).all()
    if ranges:
        range_filters = [and_(Result.position >= r.range_start, Result.position <= r.range_end) for r in ranges]
        open_result_tasks_query = open_result_tasks_query.filter(or_(*range_filters))
    # ------------------------------

    open_result_tasks_query = open_result_tasks_query.distinct()

    include_filters = [f.url for f in study.study_url_filters if f.include and f.url]
    if include_filters:
        open_result_tasks_query = open_result_tasks_query.filter(or_(*[Result.normalized_url.contains(clean_filter_string(f)) for f in include_filters]))
    exclude_filters = [f.url for f in study.study_url_filters if f.exclude and f.url]
    if exclude_filters:
        open_result_tasks_query = open_result_tasks_query.filter(and_(*[~Result.normalized_url.contains(clean_filter_string(f)) for f in exclude_filters]))

    valid_result_ids = [item[0] for item in open_result_tasks_query.all()]

    open_ai_tasks_query = db.session.query(Answer.result_ai_id).filter(
        Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status == 0,
        Answer.result_ai_id.isnot(None)
    ).distinct()
    valid_ai_ids = [item[0] for item in open_ai_tasks_query.all()]

    open_chatbot_tasks_query = db.session.query(Answer.result_chatbot_id).filter(
        Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status == 0,
        Answer.result_chatbot_id.isnot(None)
    ).distinct()
    valid_chatbot_ids = [item[0] for item in open_chatbot_tasks_query.all()]
    
    open_serp_tasks_query = db.session.query(Answer.result_serp_id).filter(
        Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status == 0,
        Answer.result_serp_id.isnot(None)
    ).distinct()
    valid_serp_ids = [item[0] for item in open_serp_tasks_query.all()]
    
    next_answer = db.session.query(Answer).filter(
        Answer.participant_id == participant.id,
        Answer.study_id == study.id,
        Answer.status == 0,
        or_(
            Answer.result_id.in_(valid_result_ids),
            Answer.result_ai_id.in_(valid_ai_ids),
            Answer.result_chatbot_id.in_(valid_chatbot_ids),
            Answer.result_serp_id.in_(valid_serp_ids)
        )
    ).order_by(Answer.id).first()

    if not next_answer:
        flash('Congratulations, you have completed all available assessments!', 'success')
        return redirect(url_for("assessments", participant_id=participant.id, study_id=study_id))

    task_item, task_type, answers_for_item, answers_to_update = None, None, [], []

    if next_answer.result_id:
        task_type = 'result'
        task_item = db.session.get(Result, next_answer.result_id)
        if task_item:
            has_source = (task_item.sources and task_item.sources[0] and task_item.sources[0].file_path)
            if not has_source and not study.assess_failed:
                all_duplicate_result_ids = {r.id for r in db.session.query(Result.id).filter(
                    Result.normalized_url == task_item.normalized_url, Result.study_id == study_id)}
                answers_to_skip = db.session.query(Answer).filter(
                    Answer.participant_id == participant.id, Answer.result_id.in_(all_duplicate_result_ids)).all()
                
                for answer in answers_to_skip:
                    answer.status = 2
                    answer.created_at = datetime.now()
                
                db.session.commit()
                return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))

            all_duplicate_result_ids = {r.id for r in db.session.query(Result.id).filter(
                Result.normalized_url == task_item.normalized_url, Result.study_id == study_id)}
            answers_for_item = db.session.query(Answer).filter(
                Answer.result_id == task_item.id, Answer.participant_id == participant.id
            ).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = db.session.query(Answer).filter(
                Answer.participant_id == participant.id, Answer.result_id.in_(all_duplicate_result_ids)).all()

    elif next_answer.result_ai_id:
        task_type = 'result_ai'
        task_item = db.session.query(ResultAi).options(joinedload(ResultAi.sources)).get(next_answer.result_ai_id)
        if task_item:
            answers_for_item = db.session.query(Answer).filter(
                Answer.result_ai_id == task_item.id, Answer.participant_id == participant.id
            ).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = answers_for_item

    elif next_answer.result_chatbot_id:
        task_type = 'result_chatbot'
        task_item = db.session.get(ResultChatbot, next_answer.result_chatbot_id)
        if task_item:
            answers_for_item = db.session.query(Answer).filter(
                Answer.result_chatbot_id == task_item.id, Answer.participant_id == participant.id
            ).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = answers_for_item

    elif next_answer.result_serp_id:
        task_type = 'serp'
        task_item = db.session.get(Serp, next_answer.result_serp_id)
        if task_item:
            answers_for_item = db.session.query(Answer).filter(
                Answer.result_serp_id == task_item.id, Answer.participant_id == participant.id
            ).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = answers_for_item
    
    if not task_item:
        flash("A critical error occurred while selecting the next task. Skipping.", "danger")
        next_answer.status = 2
        db.session.commit()
        return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))

    questions_count = len(study.questions) or 1
    total_answers_query = db.session.query(Answer.id).filter(
        Answer.participant_id == participant.id, Answer.study_id == study.id)
    all_tasks_count = total_answers_query.count() // questions_count
    closed_tasks_count = total_answers_query.filter(Answer.status.in_([1, 2])).count() // questions_count
    pct = round((closed_tasks_count / all_tasks_count * 100) if all_tasks_count > 0 else 0)

    form = FlaskForm()
    if request.method == 'POST':
        submitted_values = {}
        for q in study.questions:
            field_name = f'question_{q.id}'
            if q.questiontype.display == 'multiple_choice':
                submitted_values[q.id] = ",".join(request.form.getlist(field_name))
            else:
                submitted_values[q.id] = request.form.get(field_name, '')
        
        if 'skip' in request.form:
            for answer in answers_to_update:
                answer.status = 2; answer.created_at = datetime.now()
            db.session.commit()
            flash('This item has been skipped.', 'info')
            return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))
        
        elif 'submit' in request.form:
            validation_ok, errors = True, {}
            for answer in answers_for_item:
                q = answer.question
                is_optional = q.questiontype.display in ['short_text', 'long_text', 'scale_number']
                if not is_optional and not submitted_values.get(q.id):
                    validation_ok = False; errors[q.id] = "This field is required."
            
            if validation_ok:
                resulttype_id = None
                if task_type == 'result': resulttype_id = 1
                elif task_type == 'result_ai': resulttype_id = 2
                elif task_type == 'result_chatbot': resulttype_id = 4
                elif task_type == 'serp': resulttype_id = 5
                
                for answer in answers_to_update:
                    answer.value = submitted_values.get(answer.question_id, '')
                    answer.status = 1; answer.created_at = datetime.now()
                    if resulttype_id: answer.resulttype = resulttype_id
                db.session.commit()
                flash('Your assessments have been saved.', 'success')
                return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))
            else:
                flash("Please complete all required fields.", "danger")
                return render_template('assessments/assessment.html',
                                       form=form, answers=answers_for_item, task_item=task_item, task_type=task_type,
                                       all=all_tasks_count, closed=closed_tasks_count, pct=pct,
                                       show_urls=study.show_urls, study=study, errors=errors, submitted_data=request.form)

    return render_template('assessments/assessment.html', form=form, answers=answers_for_item,
                           task_item=task_item, task_type=task_type, all=all_tasks_count,
                           closed=closed_tasks_count, pct=pct, show_urls=study.show_urls,
                           study=study, errors={}, submitted_data={})

@app.route('/serp_image/<int:id>')
def serp_image(id):
    serp = Serp.query.get_or_404(id)
    if not serp.file_path:
        return "No file", 404
    
    zip_path = os.path.join('/var/www/rat/storage/sources', serp.file_path)
    
    if not os.path.exists(zip_path):
        return "Not found", 404
        
    try:
        import zipfile, io
        from flask import send_file
        with zipfile.ZipFile(zip_path, 'r') as z:
            if 'screenshot.jpg' in z.namelist():
                img_data = z.read('screenshot.jpg')
                return send_file(io.BytesIO(img_data), mimetype='image/jpeg')
    except Exception as e:
        return str(e), 500
        
    return "Error", 500