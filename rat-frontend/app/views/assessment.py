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
from flask import send_file

from werkzeug.utils import secure_filename
from itsdangerous import URLSafeSerializer, BadSignature
import time # Ensure time is imported!

def get_signed_storage_url(file_path, file_type='screenshot'):
    api_key = current_app.config.get('API_UPLOAD_KEY')
    base_url = current_app.config.get('STORAGE_BASE_URL')
    
    # 1. Switch to the standard URLSafeSerializer
    serializer = URLSafeSerializer(api_key)
    
    # 2. Manually calculate expiration (e.g., +300 seconds / 5 mins)
    expires_at = int(time.time()) + 300
    
    # 3. Add the expires_at timestamp into the payload dictionary
    ticket = serializer.dumps({'filename': file_path, 'expires_at': expires_at}, salt='source-view')
    
    return f"{base_url}/view/{file_path}/{file_type}?ticket={ticket}"


@app.context_processor
def inject_storage_urls():
    return dict(get_storage_url=get_signed_storage_url)

@app.route('/study/<study_id>/assessments/<participant_id>', methods=["GET", "POST"])
def assessments(study_id, participant_id):
    logout_user()
    study = Study.query.get_or_404(study_id)
    participant = Participant.query.get_or_404(participant_id)
    
    # 1. Fetch current active task for this participant
    answers_for_item = Answer.query.filter_by(
        participant_id=participant_id, 
        study_id=study_id, 
        status=0
    ).order_by(Answer.id).all()

    # 2. Redirect safely if the queue is empty
    if not answers_for_item:
        flash('You have completed all your assigned assessments. Thank you!', 'success')
        # Redirects them to a safe place (you can change this to index/home if you prefer)
        return redirect(url_for('returning_participant', study_id=study_id)) 

    # 3. Identify the current task properties
    task_item = None
    task_type = None
    resulttype_id = answers_for_item[0].resulttype

    if answers_for_item[0].result_id:
        task_item = answers_for_item[0].result
        task_type = 'result'
    elif answers_for_item[0].result_ai_id:
        task_item = answers_for_item[0].result_ai
        task_type = 'ai'
    elif answers_for_item[0].result_chatbot_id:
        task_item = answers_for_item[0].result_chatbot
        task_type = 'chatbot'
    elif answers_for_item[0].result_serp:
        task_item = answers_for_item[0].result_serp
        task_type = 'serp'

    # 4. Handle the Submission
    if request.method == "POST":
        submitted_values = {}
        
        # Save answers for the current item
        for answer in answers_for_item:
            val = request.form.get(str(answer.question_id))
            if isinstance(val, list): 
                val = ",".join(val) # For multi-select fields
                
            if val:
                answer.value = val
                answer.status = 1
                answer.created_at = datetime.now()
                submitted_values[answer.question_id] = val
        
        # --- QUERY-AWARE AUTO-MIRRORING HOOK ---
        if task_type == 'result' and hasattr(task_item, 'normalized_url') and task_item.normalized_url:
            q_obj = getattr(task_item, 'query_', None) # FIX: Use query_
            
            if q_obj:
                # Find matching results with same normalized_url AND same batch timestamp
                duplicates = Result.query.join(Query).filter(
                    Result.study_id == study_id,
                    Result.normalized_url == task_item.normalized_url,
                    Query.created_at == q_obj.created_at,
                    Result.id != task_item.id
                ).all()
                
                if duplicates:
                    dup_ids = [d.id for d in duplicates]
                    
                    # Find any pending mirrored answers assigned to this specific participant
                    dup_answers = Answer.query.filter(
                        Answer.participant_id == participant_id,
                        Answer.status == 0,
                        Answer.result_id.in_(dup_ids)
                    ).all()
                    
                    # Mirror the values quietly
                    for dup in dup_answers:
                        if dup.question_id in submitted_values:
                            dup.value = submitted_values[dup.question_id]
                            dup.status = 1
                            dup.created_at = datetime.now()
                            if resulttype_id: 
                                dup.resulttype = resulttype_id

        db.session.commit()
        flash('Assessment saved successfully.', 'success')
        return redirect(url_for('assessments', participant_id=participant_id, study_id=study_id))

    # 5. Calculate Progress Statistics for the template
    # Because Answer rows are generated per-question, we divide by questions to get "tasks"
    questions_count = len(study.questions) if study.questions else 1
    
    total_answer_rows = Answer.query.filter_by(participant_id=participant_id, study_id=study_id).count()
    closed_answer_rows = Answer.query.filter_by(participant_id=participant_id, study_id=study_id, status=1).count()
    
    all_tasks_count = total_answer_rows // questions_count
    closed_tasks_count = closed_answer_rows // questions_count
    pct = (closed_tasks_count / all_tasks_count) * 100 if all_tasks_count > 0 else 0
    
    return render_template('assessments/assessment.html', 
                           answers=answers_for_item, 
                           task_item=task_item, 
                           task_type=task_type,
                           all=all_tasks_count, 
                           closed=closed_tasks_count, 
                           pct=round(pct), 
                           show_urls=study.show_urls, 
                           study=study, 
                           errors={}, 
                           submitted_data={})



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
        flash('Congratulations, you have completed all available assessments!', 'success')
        return redirect(url_for("assessments", participant_id=participant.id, study_id=study_id))

    task_item, task_type, answers_for_item, answers_to_update = None, None, [], []

    if next_answer.result_id:
        task_type = 'result'
        task_item = db.session.get(Result, next_answer.result_id)
        if task_item:
            # --- QUERY-AWARE DUPLICATE DETECTION ---
            q_obj = getattr(task_item, 'query_', None)
            
            all_duplicate_result_ids = set()
            # Filter strictly by the query's batch timestamp
            if q_obj and task_item.normalized_url:
                # FIX: Find items with the same URL, in the same upload batch (timestamp)
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
            
            # 1. Define the full set of IDs to update (Current + Duplicates)
            target_ids = all_duplicate_result_ids.union({task_item.id})
            
            # 2. Safely query for updates
            if target_ids:
                answers_to_update = db.session.query(Answer).filter(
                    Answer.participant_id == participant.id, 
                    Answer.result_id.in_(target_ids)
                ).all()
            else:
                # Fallback for safety (though with the union, target_ids should never be empty)
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
    
    signed_url = get_signed_storage_url(serp.file_path, file_type='screenshot')
    
    return redirect(signed_url)