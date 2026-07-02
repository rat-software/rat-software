from .. import app, db, csrf
from ..models import Study, Participant, Answer, Question, Result, ResultAi, ResultChatbot, ResultSource, Serp, RangeStudy, Query, ResultType
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
import random

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
    
    closed_answer_rows = Answer.query.filter(
        Answer.participant_id == participant_id, 
        Answer.study_id == study_id, 
        Answer.status.in_([1, 2])
    ).count()
    
    answers_closed = closed_answer_rows // questions_count
    
    if study.limit_by_query and (study.max_queries_per_participant or 0) > 0:
        answers_all = study.max_queries_per_participant
    elif study.limit_per_participant and (study.max_results_per_participant or 0) > 0:
        answers_all = study.max_results_per_participant
    else:
        answers_all = answers_closed 
        
    pct = round((answers_closed / answers_all) * 100) if answers_all > 0 else 100
    if pct > 100: pct = 100
    
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
        # 1. Wir ermitteln, was der Nutzer bereits gesehen hat
        completed_answers = db.session.query(Answer).filter(
            Answer.participant_id == participant.id,
            Answer.study_id == study.id,
            Answer.status.in_([1, 2])
        ).all()
        
        seen_queries = set()
        seen_items_count = 0
        first_question_id = study.questions[0].id if study.questions else None
        
        for ans in completed_answers:
            if first_question_id and ans.question_id == first_question_id: 
                seen_items_count += 1
            if ans.result_id and ans.result.query_id: seen_queries.add(ans.result.query_id)
            elif ans.result_ai_id and ans.result_ai.query_id: seen_queries.add(ans.result_ai.query_id)
            elif ans.result_chatbot_id and ans.result_chatbot.query_id: seen_queries.add(ans.result_chatbot.query_id)
            elif ans.result_serp_id and ans.result_serp.query_id: seen_queries.add(ans.result_serp.query_id)
            
        limit_reached = False
        if study.group_by_query and study.limit_by_query and study.max_queries_per_participant != -1:
            max_q = study.max_queries_per_participant if (study.max_queries_per_participant and study.max_queries_per_participant > 0) else 99999
            if len(seen_queries) >= max_q: limit_reached = True

        if study.limit_per_participant and study.max_results_per_participant is not None:
            max_i = study.max_results_per_participant if study.max_results_per_participant > 0 else 99999
            if seen_items_count >= max_i: limit_reached = True
            
        if not limit_reached:
            allowed_types = [t.strip().lower() for t in study.assessable_result_types_text.split(',')] if study.assessable_result_types_text else []
            res_types_map = {rt.name.strip().lower(): rt.id for rt in db.session.query(ResultType).all()}
            assigned_successfully = False

            if study.group_by_query:
                available_queries = db.session.query(Query).filter(
                    Query.study_id == study.id,
                    ~Query.id.in_(seen_queries if seen_queries else [-1])
                ).all()
                if available_queries:
                    available_queries.sort(key=lambda q: (
                        db.session.query(Answer).filter(
                            Answer.study_id == study.id,
                            or_(Answer.result_id.in_(db.session.query(Result.id).filter_by(query_id=q.id)),
                                Answer.result_ai_id.in_(db.session.query(ResultAi.id).filter_by(query_id=q.id)),
                                Answer.result_chatbot_id.in_(db.session.query(ResultChatbot.id).filter_by(query_id=q.id)),
                                Answer.result_serp_id.in_(db.session.query(Serp.id).filter_by(query_id=q.id)))
                        ).count(), random.random()
                    ))
                    for candidate_query in available_queries:
                        locked_query = db.session.query(Query).filter_by(id=candidate_query.id).with_for_update(skip_locked=True).first()
                        if locked_query:
                            items_to_assign = []
                            if 'organic' in allowed_types: items_to_assign.extend(db.session.query(Result).filter_by(query_id=locked_query.id).all())
                            if 'ai overview' in allowed_types or 'ai_overview' in allowed_types: items_to_assign.extend(db.session.query(ResultAi).filter_by(query_id=locked_query.id).all())
                            if 'chatbot' in allowed_types: items_to_assign.extend(db.session.query(ResultChatbot).filter_by(query_id=locked_query.id).all())
                            if 'serp' in allowed_types: items_to_assign.extend(db.session.query(Serp).filter_by(query_id=locked_query.id).all())
                            if items_to_assign:
                                random.shuffle(items_to_assign)
                                for task in items_to_assign:
                                    task_type_text = "organic"
                                    if isinstance(task, ResultAi): task_type_text = "ai overview"
                                    elif isinstance(task, ResultChatbot): task_type_text = "chatbot"
                                    elif isinstance(task, Serp): task_type_text = "serp"
                                    resolved_type_id = res_types_map.get(task_type_text, 1)
                                    for question in study.questions:
                                        ans = Answer(study_id=study.id, question_id=question.id, participant_id=participant.id, status=0, created_at=datetime.now(), resulttype=resolved_type_id, result_type_text=task_type_text)
                                        if isinstance(task, Result): ans.result = task
                                        elif isinstance(task, ResultAi): ans.result_ai = task
                                        elif isinstance(task, ResultChatbot): ans.result_chatbot = task
                                        elif isinstance(task, Serp): ans.result_serp = task
                                        db.session.add(ans)
                                db.session.commit()
                                assigned_successfully = True
                                break
                            else: db.session.commit()
            
            else:
                pools = {}
                seen_res_ids = [r[0] for r in db.session.query(Answer.result_id).filter(Answer.participant_id == participant.id, Answer.result_id.isnot(None)).all()]
                seen_ai_ids = [r[0] for r in db.session.query(Answer.result_ai_id).filter(Answer.participant_id == participant.id, Answer.result_ai_id.isnot(None)).all()]
                seen_chat_ids = [r[0] for r in db.session.query(Answer.result_chatbot_id).filter(Answer.participant_id == participant.id, Answer.result_chatbot_id.isnot(None)).all()]
                seen_serp_ids = [r[0] for r in db.session.query(Answer.result_serp_id).filter(Answer.participant_id == participant.id, Answer.result_serp_id.isnot(None)).all()]
                if 'organic' in allowed_types: pools['organic'] = db.session.query(Result).filter(Result.study_id == study.id, ~Result.id.in_(seen_res_ids if seen_res_ids else [-1])).all()
                if 'ai overview' in allowed_types or 'ai_overview' in allowed_types: pools['ai'] = db.session.query(ResultAi).filter(ResultAi.study_id == study.id, ~ResultAi.id.in_(seen_ai_ids if seen_ai_ids else [-1])).all()
                if 'chatbot' in allowed_types: pools['chatbot'] = db.session.query(ResultChatbot).filter(ResultChatbot.study_id == study.id, ~ResultChatbot.id.in_(seen_chat_ids if seen_chat_ids else [-1])).all()
                if 'serp' in allowed_types: pools['serp'] = db.session.query(Serp).filter(Serp.study_id == study.id, ~Serp.id.in_(seen_serp_ids if seen_serp_ids else [-1])).all()
                all_pool_items = []
                for p_name, items in pools.items(): all_pool_items.extend(items)
                if all_pool_items:
                    counts = db.session.query(
                        func.coalesce(Answer.result_id, Answer.result_ai_id, Answer.result_chatbot_id, Answer.result_serp_id).label('item_id'), 
                        func.count(Answer.id)
                    ).filter(Answer.study_id == study.id).group_by('item_id').all()
                    
                    count_map = {row[0]: row[1] for row in counts}
                    all_pool_items.sort(key=lambda t: (count_map.get(t.id, 0), random.random()))
                    for candidate_task in all_pool_items:
                        model_class = type(candidate_task)
                        locked_task = db.session.query(model_class).filter_by(id=candidate_task.id).with_for_update(skip_locked=True).first()
                        if locked_task:
                            task_type_text = "organic"
                            if isinstance(locked_task, ResultAi): task_type_text = "ai overview"
                            elif isinstance(locked_task, ResultChatbot): task_type_text = "chatbot"
                            elif isinstance(locked_task, Serp): task_type_text = "serp"
                            resolved_type_id = res_types_map.get(task_type_text, 1)
                            for question in study.questions:
                                ans = Answer(study_id=study.id, question_id=question.id, participant_id=participant.id, status=0, created_at=datetime.now(), resulttype=resolved_type_id, result_type_text=task_type_text)
                                if isinstance(locked_task, Result): ans.result = locked_task
                                elif isinstance(locked_task, ResultAi): ans.result_ai = locked_task
                                elif isinstance(locked_task, ResultChatbot): ans.result_chatbot = locked_task
                                elif isinstance(locked_task, Serp): ans.result_serp = locked_task
                                db.session.add(ans)
                            db.session.commit()
                            assigned_successfully = True
                            break
                            
            if assigned_successfully: return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))

        if study.post_survey_json and study.post_survey_json.strip() not in ['', '[]']:
            post_answers_dict = {}
            if participant.post_survey_answers:
                try: post_answers_dict = json.loads(participant.post_survey_answers)
                except: pass
            if str(study.id) not in post_answers_dict: return redirect(url_for('dynamic_survey', study_id=study.id, survey_type='post', participant_id=participant.id))
        return redirect(url_for("assessments", participant_id=participant.id, study_id=study.id))

    task_item, task_type, answers_for_item, answers_to_update = None, None, [], []
    if next_answer.result_id:
        task_type = 'result'
        task_item = db.session.get(Result, next_answer.result_id)
        if task_item:
            q_obj = getattr(task_item, 'query_', None)
            all_duplicate_result_ids = set()
            if q_obj and task_item.normalized_url:
                duplicates = Result.query.join(Query).filter(Result.study_id == study_id, Result.normalized_url == task_item.normalized_url, Query.created_at == q_obj.created_at, Result.id != task_item.id).all()
                all_duplicate_result_ids = {d.id for d in duplicates}
            has_source = (task_item.sources and task_item.sources[0] and task_item.sources[0].file_path)
            if not has_source and not study.assess_failed:
                if all_duplicate_result_ids:
                    answers_to_skip = db.session.query(Answer).filter(Answer.participant_id == participant.id, Answer.result_id.in_(all_duplicate_result_ids)).all()
                    for answer in answers_to_skip: answer.status = 2; answer.created_at = datetime.now()
                    db.session.commit()
                return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))
            answers_for_item = db.session.query(Answer).filter(Answer.result_id == task_item.id, Answer.participant_id == participant.id).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            target_ids = all_duplicate_result_ids.union({task_item.id})
            answers_to_update = db.session.query(Answer).filter(Answer.participant_id == participant.id, Answer.result_id.in_(target_ids)).all() if target_ids else answers_for_item
    elif next_answer.result_ai_id:
        task_type = 'result_ai'
        task_item = db.session.query(ResultAi).options(joinedload(ResultAi.sources)).get(next_answer.result_ai_id)
        if task_item:
            answers_for_item = db.session.query(Answer).filter(Answer.result_ai_id == task_item.id, Answer.participant_id == participant.id).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = answers_for_item
    elif next_answer.result_chatbot_id:
        task_type = 'result_chatbot'
        task_item = db.session.get(ResultChatbot, next_answer.result_chatbot_id)
        if task_item:
            answers_for_item = db.session.query(Answer).filter(Answer.result_chatbot_id == task_item.id, Answer.participant_id == participant.id).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = answers_for_item
    elif next_answer.result_serp_id:
        task_type = 'serp'
        task_item = db.session.get(Serp, next_answer.result_serp_id)
        if task_item:
            answers_for_item = db.session.query(Answer).filter(Answer.result_serp_id == task_item.id, Answer.participant_id == participant.id).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = answers_for_item
    
    if not task_item:
        next_answer.status = 2; db.session.commit()
        return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))

    questions_count = len(study.questions) or 1
    closed_tasks_count = db.session.query(Answer.id).filter(Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status.in_([1, 2])).count() // questions_count
    all_tasks_count = study.max_queries_per_participant if (study.limit_by_query and study.max_queries_per_participant or 0) > 0 else (study.max_results_per_participant if (study.limit_per_participant and study.max_results_per_participant or 0) > 0 else closed_tasks_count + 1)
    pct = round((closed_tasks_count / all_tasks_count * 100) if all_tasks_count > 0 else 0)
    if pct > 100: pct = 100

    form = FlaskForm()
    if request.method == 'POST':
        submitted_values = {q.id: (",".join(request.form.getlist(f'question_{q.id}')) if q.questiontype.display == 'multiple_choice' else request.form.get(f'question_{q.id}', '')) for q in study.questions}
        if 'skip' in request.form:
            for answer in answers_to_update: answer.status = 2; answer.created_at = datetime.now()
            db.session.commit()
            return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))
        elif 'submit' in request.form:
            validation_ok, errors = True, {}
            for answer in answers_for_item:
                if answer.question.questiontype.display not in ['short_text', 'long_text', 'scale_number'] and not submitted_values.get(answer.question_id):
                    validation_ok = False; errors[answer.question_id] = "Required."
            if validation_ok:
                rt_map = {'result': 1, 'result_ai': 2, 'result_chatbot': 4, 'serp': 5}
                for answer in answers_to_update:
                    answer.value = submitted_values.get(answer.question_id, ''); answer.status = 1; answer.created_at = datetime.now(); answer.resulttype = rt_map.get(task_type, 1)
                db.session.commit()
                return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))
            return render_template('assessments/assessment.html', form=form, answers=answers_for_item, task_item=task_item, task_type=task_type, all=all_tasks_count, closed=closed_tasks_count, pct=pct, show_urls=study.show_urls, study=study, errors=errors, submitted_data=request.form)

    return render_template('assessments/assessment.html', form=form, answers=answers_for_item, task_item=task_item, task_type=task_type, all=all_tasks_count, closed=closed_tasks_count, pct=pct, show_urls=study.show_urls, study=study, errors={}, submitted_data={})

@app.route('/serp_image/<int:id>')
def serp_image(id):
    serp = Serp.query.get_or_404(id)
    if not serp.file_path: return "No file", 404
    return redirect(get_signed_storage_url(serp.file_path, file_type='screenshot'))

@app.route('/study/<study_id>/survey/<survey_type>/<participant_id>', methods=['GET', 'POST'])
def dynamic_survey(study_id, survey_type, participant_id):
    logout_user()
    study = Study.query.get_or_404(study_id)
    participant = Participant.query.get_or_404(participant_id)
    json_data = study.pre_survey_json if survey_type == 'pre' else study.post_survey_json
    questions = json.loads(json_data) if json_data else []
    if request.method == 'POST':
        submitted = {q['id']: request.form.getlist(q['id']) if q['type'] == 'multiple_choice' else request.form.get(q['id'], '') for q in questions}
        ans_dict = json.loads(participant.pre_survey_answers if survey_type == 'pre' else participant.post_survey_answers) if (participant.pre_survey_answers if survey_type == 'pre' else participant.post_survey_answers) else {}
        ans_dict[str(study.id)] = submitted
        if survey_type == 'pre': participant.pre_survey_answers = json.dumps(ans_dict)
        else: participant.post_survey_answers = json.dumps(ans_dict)
        db.session.commit()
        return redirect(url_for('assessment', participant_id=participant.id, study_id=study.id))
    return render_template('surveys/survey.html', title=f"{survey_type.capitalize()}-Survey", questions=questions, study=study)