from .. import app, db, csrf
from ..models import Study, Participant, Answer, Question, Result, ResultAi, ResultChatbot, ResultSource, Serp, RangeStudy, Query
from flask import render_template, flash, redirect, url_for, request
from flask_login import logout_user
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_, and_
from flask_wtf import FlaskForm
from ..helpers import clean_filter_string

from flask import current_app

import os
import zipfile
import io
import json
from flask import send_file

from werkzeug.utils import secure_filename
from itsdangerous import URLSafeSerializer, BadSignature
import time 

def get_signed_storage_url(file_path, file_type='screenshot'):
    api_key = current_app.config.get('API_UPLOAD_KEY')
    base_url = current_app.config.get('STORAGE_BASE_URL')
    
    serializer = URLSafeSerializer(api_key)
    expires_at = int(time.time()) + 300
    ticket = serializer.dumps({'filename': file_path, 'expires_at': expires_at}, salt='source-view')
    
    return f"{base_url}/view/{file_path}/{file_type}?ticket={ticket}"


@app.context_processor
def inject_storage_urls():
    return dict(get_storage_url=get_signed_storage_url)

# ==========================================================
# --- FORTSCHRITTS- UND ABSCHLUSS-SEITE ---
# ==========================================================
@app.route('/study/<study_id>/assessments/<participant_id>', methods=["GET", "POST"])
def assessments(study_id, participant_id):
    logout_user()
    study = Study.query.get_or_404(study_id)
    participant = Participant.query.get_or_404(participant_id)
    
    questions_count = len(study.questions) if study.questions else 1
    
    # Berechnet den echten Fortschritt
    total_answer_rows = Answer.query.filter_by(participant_id=participant_id, study_id=study_id).count()
    closed_answer_rows = Answer.query.filter(
        Answer.participant_id == participant_id, 
        Answer.study_id == study_id, 
        Answer.status.in_([1, 2])
    ).count()
    
    answers_all = total_answer_rows // questions_count
    answers_closed = closed_answer_rows // questions_count
    pct = round((answers_closed / answers_all) * 100) if answers_all > 0 else 0
    
    # Lädt das Template assessments.html -> Hier wird dein Completion Text angezeigt!
    return render_template('assessments/assessments.html', 
                           study=study, 
                           participant=participant,
                           answers_all=answers_all, 
                           answers_closed=answers_closed, 
                           pct=pct)

# ==========================================================
# --- HAUPT-AUFGABEN-SCHLEIFE (ROUTING) ---
# ==========================================================
@app.route('/assessment/<participant_id>/<study_id>', methods=["GET", "POST"])
def assessment(participant_id, study_id):
    logout_user()
    participant = Participant.query.get_or_404(participant_id)
    study = Study.query.get_or_404(study_id)
    db.session.expire_all()

    # --- ONBOARDING & PRE-SURVEY INTERCEPTION ---
    total_answers = Answer.query.filter_by(participant_id=participant.id, study_id=study.id, status=1).count()
    
    pre_answers_dict = {}
    if participant.pre_survey_answers:
        try: pre_answers_dict = json.loads(participant.pre_survey_answers)
        except: pass
    
    has_pre_answers = str(study.id) in pre_answers_dict
    
    if study.show_description_after_join and not has_pre_answers and total_answers == 0:
        if not request.args.get('seen_welcome'):
            next_url = url_for('assessment', participant_id=participant.id, study_id=study.id, seen_welcome=1)
            return render_template('surveys/welcome.html', study=study, participant=participant, next_url=next_url)

    if study.pre_survey_json and study.pre_survey_json.strip() not in ['', '[]']:
        if not has_pre_answers:
            return redirect(url_for('dynamic_survey', study_id=study.id, survey_type='pre', participant_id=participant.id))

    # --- RESULT QUERY LOGIC ---
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

    ranges = RangeStudy.query.filter_by(study=study.id).all()
    if ranges:
        range_filters = [and_(Result.position >= r.range_start, Result.position <= r.range_end) for r in ranges]
        open_result_tasks_query = open_result_tasks_query.filter(or_(*range_filters))

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
        # --- POST-SURVEY INTERCEPTION ---
        if study.post_survey_json and study.post_survey_json.strip() not in ['', '[]']:
            post_answers_dict = {}
            if participant.post_survey_answers:
                try: post_answers_dict = json.loads(participant.post_survey_answers)
                except: pass
            
            if str(study.id) not in post_answers_dict:
                return redirect(url_for('dynamic_survey', study_id=study.id, survey_type='post', participant_id=participant.id))

        # --- FERTIG! LEITE ZUR ABSCHLUSSSEITE WEITER ---
        # Keine flash-Message mehr, das macht die UI jetzt schöner
        return redirect(url_for("assessments", participant_id=participant.id, study_id=study_id))

    task_item, task_type, answers_for_item, answers_to_update = None, None, [], []

    if next_answer.result_id:
        task_type = 'result'
        task_item = db.session.get(Result, next_answer.result_id)
        if task_item:
            q_obj = getattr(task_item, 'query_', None)
            
            all_duplicate_result_ids = set()
            if q_obj and task_item.normalized_url:
                duplicates = Result.query.join(Query).filter(
                    Result.study_id == study_id,
                    Result.normalized_url == task_item.normalized_url,
                    Query.created_at == q_obj.created_at,
                    Result.id != task_item.id
                ).all()
                all_duplicate_result_ids = {d.id for d in duplicates}

            has_source = (task_item.sources and task_item.sources[0] and task_item.sources[0].file_path)
            
            if not has_source and not study.assess_failed:
                if all_duplicate_result_ids:
                    answers_to_skip = db.session.query(Answer).filter(
                        Answer.participant_id == participant.id, Answer.result_id.in_(all_duplicate_result_ids)).all()
                    
                    for answer in answers_to_skip:
                        answer.status = 2
                        answer.created_at = datetime.now()
                    
                    db.session.commit()
                return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))

            answers_for_item = db.session.query(Answer).filter(
                Answer.result_id == task_item.id, Answer.participant_id == participant.id
            ).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            
            target_ids = all_duplicate_result_ids.union({task_item.id})
            
            if target_ids:
                answers_to_update = db.session.query(Answer).filter(
                    Answer.participant_id == participant.id, 
                    Answer.result_id.in_(target_ids)
                ).all()
            else:
                answers_to_update = answers_for_item

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
                # Flash message entfernt für einen flüssigeren Übergang ohne störende Banner
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
    signed_url = get_signed_storage_url(serp.file_path, file_type='screenshot')
    return redirect(signed_url)


# ==============================================================================
# DYNAMIC SURVEY ROUTING (PRE- AND POST-SURVEYS)
# ==============================================================================
@app.route('/study/<study_id>/survey/<survey_type>/<participant_id>', methods=['GET', 'POST'])
def dynamic_survey(study_id, survey_type, participant_id):
    logout_user()
    study = Study.query.get_or_404(study_id)
    participant = Participant.query.get_or_404(participant_id)
    
    if survey_type == 'pre':
        json_data = study.pre_survey_json
        title = "Pre-Assessment Questionnaire"
        description = "Please answer the following questions before starting the evaluation."
    else:
        json_data = study.post_survey_json
        title = "Post-Assessment Questionnaire"
        description = "Thank you for your evaluations! Please answer these final questions."
        
    questions = []
    if json_data:
        try:
            questions = json.loads(json_data)
        except Exception as e:
            flash(f"Error loading survey format: {e}", "danger")
            
    if request.method == 'POST':
        submitted = {}
        for q in questions:
            q_id = q['id']
            if q['type'] == 'multiple_choice':
                val = request.form.getlist(q_id)
                submitted[q_id] = val
            else:
                submitted[q_id] = request.form.get(q_id, '')
                
        db_field = participant.pre_survey_answers if survey_type == 'pre' else participant.post_survey_answers
        ans_dict = {}
        if db_field:
            try: ans_dict = json.loads(db_field)
            except: pass
            
        ans_dict[str(study.id)] = submitted
        
        if survey_type == 'pre':
            participant.pre_survey_answers = json.dumps(ans_dict)
        else:
            participant.post_survey_answers = json.dumps(ans_dict)
            
        db.session.commit()
        return redirect(url_for('assessment', participant_id=participant.id, study_id=study.id))
        
    return render_template('surveys/survey.html', title=title, description=description, questions=questions, study=study)