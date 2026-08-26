"""
Assessment module for the RAT application.

This module handles participant-facing tasks, including onboarding screens, 
pre- and post-study surveys, progress tracking dashboards, and the core 
evaluation loop that assigns and updates answers for standard organic text 
results, SERP views, chatbot responses, AI summaries, and Image results.
"""

from app.views.question import questions

from .. import app, db, csrf
from ..models import Study, Participant, Answer, Question, Result, ResultAi, ResultChatbot, ResultSource, Serp, RangeStudy, Query, ResultType, ResultAiSource, ResultImage
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
    """
    Generates a cryptographically signed and timed token URL to fetch storage server files.

    Args:
        file_path (str): Relative or absolute target file path inside the storage repository.
        file_type (str): Category type designation (e.g., 'screenshot' or 'code'). Defaults to 'screenshot'.

    Returns:
        str: Fully qualified storage request destination combined with the security ticket parameter.
    """
    api_key = current_app.config.get('API_UPLOAD_KEY')
    base_url = current_app.config.get('STORAGE_BASE_URL')
    
    serializer = URLSafeSerializer(api_key)
    expires_at = int(time.time()) + 300
    ticket = serializer.dumps({'filename': file_path, 'expires_at': expires_at}, salt='source-view')
    
    return f"{base_url}/view/{file_path}/{file_type}?ticket={ticket}"


@app.context_processor
def inject_storage_urls():
    """
    Flask context processor to make storage URL signing available globally across all Jinja templates.
    """
    return dict(get_storage_url=get_signed_storage_url)

@app.route('/study/<study_id>/assessments/<participant_id>', methods=["GET", "POST"])
def assessments(study_id, participant_id):
    """
    Renders the central progress status panel and completion dashboard for a participant.
    """
    logout_user()
    study = Study.query.get_or_404(study_id)
    participant = Participant.query.get_or_404(participant_id)
    
    questions_count = len(study.questions) if study.questions else 1
    
    if study.group_by_query:
        all_answers = Answer.query.filter_by(participant_id=participant_id, study_id=study_id).all()
        seen_queries = set()
        open_queries = set()
        
        for ans in all_answers:
            q_id = None
            if ans.result_id and ans.result.query_id: q_id = ans.result.query_id
            elif ans.result_ai_id and ans.result_ai.query_id: q_id = ans.result_ai.query_id
            elif ans.result_chatbot_id and ans.result_chatbot.query_id: q_id = ans.result_chatbot.query_id
            elif ans.result_serp_id and ans.result_serp.query_id: q_id = ans.result_serp.query_id
            elif ans.result_ai_source_id and ans.result_ai_source.query_id: q_id = ans.result_ai_source.query_id
            elif ans.result_image_id and ans.result_image.query_id: q_id = ans.result_image.query_id
            
            if q_id:
                seen_queries.add(q_id)
                if ans.status == 0:
                    open_queries.add(q_id)
                    
        answers_closed = len(seen_queries) - len(open_queries)
        answers_open = len(open_queries)
        
        if (study.max_queries_per_participant or 0) > 0:
            answers_all = study.max_queries_per_participant
            if (answers_closed + answers_open) > answers_all:
                answers_all = answers_closed + answers_open
        else:
            answers_all = answers_closed + answers_open
            
        if answers_all == 0: answers_all = 1
            
    else:
        closed_answer_rows = Answer.query.filter(
            Answer.participant_id == participant_id, 
            Answer.study_id == study_id, 
            Answer.status.in_([1, 2])
        ).count()
        
        open_answer_rows = Answer.query.filter(
            Answer.participant_id == participant_id, 
            Answer.study_id == study_id, 
            Answer.status == 0
        ).count()
        
        answers_closed = closed_answer_rows // questions_count
        answers_open = open_answer_rows // questions_count
        
        if study.limit_per_participant and (study.max_results_per_participant or 0) > 0:
            answers_all = study.max_results_per_participant
            if (answers_closed + answers_open) > answers_all:
                answers_all = answers_closed + answers_open
        else:
            answers_all = answers_closed + answers_open
            
        if answers_all == 0:
            answers_all = 1
            
    pct = round((answers_closed / answers_all) * 100) if answers_all > 0 else 0
    if pct > 100: pct = 100
    
    return render_template('assessments/assessments.html', 
                           study=study, 
                           participant=participant,
                           answers_all=answers_all, 
                           answers_closed=answers_closed, 
                           pct=pct)

# ==========================================================
# --- MAIN TASK LOOP (ROUTING) ---
# ==========================================================
@app.route('/assessment/<participant_id>/<study_id>', methods=["GET", "POST"])
def assessment(participant_id, study_id):
    logout_user()
    participant = Participant.query.get_or_404(participant_id)
    study = Study.query.get_or_404(study_id)
    db.session.expire_all()

    # --- ONBOARDING & PRE-SURVEY INTERCEPTION ---
    total_answers = Answer.query.filter_by(participant_id=participant.id, study_id=study.id).count()
    
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

    # --- RESULT QUERY LOGIC (Filter für Anzeige falls sich Settings nach Start ändern) ---
    ranges = RangeStudy.query.filter_by(study=study.id).all()
    include_filters = [f.url for f in study.study_url_filters if f.include and f.url]
    exclude_filters = [f.url for f in study.study_url_filters if f.exclude and f.url]

    # 1. ORGANIC RESULTS
    open_res_q = db.session.query(Answer.result_id).filter(
        Answer.participant_id == participant.id,
        Answer.study_id == study.id,
        Answer.status == 0,
        Answer.result_id.isnot(None)
    ).join(Result)
    
    if not study.live_link_mode:
        open_res_q = open_res_q.join(Result.source_associations)
        if study.assess_failed:
            open_res_q = open_res_q.filter(or_(ResultSource.progress == 1, ResultSource.progress == -1))
        else:
            open_res_q = open_res_q.filter(ResultSource.progress == 1)
        
    if study.result_count:
        open_res_q = open_res_q.filter(Result.position <= study.result_count)
        
    open_result_tasks_query = open_res_q.filter(Result.normalized_url.isnot(None), Result.normalized_url != "")

    if ranges:
        range_filters = [and_(Result.position >= r.range_start, Result.position <= r.range_end) for r in ranges]
        open_result_tasks_query = open_result_tasks_query.filter(or_(*range_filters))

    open_result_tasks_query = open_result_tasks_query.distinct()

    if include_filters:
        open_result_tasks_query = open_result_tasks_query.filter(or_(*[Result.normalized_url.contains(clean_filter_string(f)) for f in include_filters]))
    if exclude_filters:
        open_result_tasks_query = open_result_tasks_query.filter(and_(*[~Result.normalized_url.contains(clean_filter_string(f)) for f in exclude_filters]))

    valid_result_ids = [item[0] for item in open_result_tasks_query.all()]

    # 2. AI OVERVIEW
    open_ai_tasks_query = db.session.query(Answer.result_ai_id).filter(
        Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status == 0, Answer.result_ai_id.isnot(None)
    ).distinct()
    valid_ai_ids = [item[0] for item in open_ai_tasks_query.all()]
    
    # 3. AI SOURCES (Citations)
    open_ai_source_tasks_query = db.session.query(Answer.result_ai_source_id).filter(
        Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status == 0, Answer.result_ai_source_id.isnot(None)
    ).join(ResultAiSource, Answer.result_ai_source_id == ResultAiSource.id)

    if not study.live_link_mode:
        if study.assess_failed:
            open_ai_source_tasks_query = open_ai_source_tasks_query.filter(or_(ResultAiSource.progress == 1, ResultAiSource.progress == -1))
        else:
            open_ai_source_tasks_query = open_ai_source_tasks_query.filter(ResultAiSource.progress == 1)

    if study.result_count:
        open_ai_source_tasks_query = open_ai_source_tasks_query.filter(ResultAiSource.position <= study.result_count)

    if ranges:
        ai_src_range_filters = [and_(ResultAiSource.position >= r.range_start, ResultAiSource.position <= r.range_end) for r in ranges]
        open_ai_source_tasks_query = open_ai_source_tasks_query.filter(or_(*ai_src_range_filters))

    open_ai_source_tasks_query = open_ai_source_tasks_query.distinct()
    valid_ai_source_ids = [item[0] for item in open_ai_source_tasks_query.all()]

    # 4. CHATBOTS
    open_chatbot_tasks_query = db.session.query(Answer.result_chatbot_id).filter(
        Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status == 0, Answer.result_chatbot_id.isnot(None)
    ).distinct()
    valid_chatbot_ids = [item[0] for item in open_chatbot_tasks_query.all()]
    
    # 5. SERPs
    open_serp_tasks_query = db.session.query(Answer.result_serp_id).filter(
        Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status == 0, Answer.result_serp_id.isnot(None)
    ).distinct()
    valid_serp_ids = [item[0] for item in open_serp_tasks_query.all()]

    # 6. IMAGE TASKS
    open_image_tasks_query = db.session.query(Answer.result_image_id).filter(
        Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status == 0, Answer.result_image_id.isnot(None)
    ).join(ResultImage, Answer.result_image_id == ResultImage.id)
    
    if not study.live_link_mode:
        if study.assess_failed:
            open_image_tasks_query = open_image_tasks_query.filter(or_(ResultImage.progress == 1, ResultImage.progress == -1))
        else:
            open_image_tasks_query = open_image_tasks_query.filter(ResultImage.progress == 1)

    if study.result_count:
        open_image_tasks_query = open_image_tasks_query.filter(ResultImage.position <= study.result_count)

    if ranges:
        img_range_filters = [and_(ResultImage.position >= r.range_start, ResultImage.position <= r.range_end) for r in ranges]
        open_image_tasks_query = open_image_tasks_query.filter(or_(*img_range_filters))

    open_image_tasks_query = open_image_tasks_query.distinct()
    valid_image_ids = [item[0] for item in open_image_tasks_query.all()]
    
    # --- GET NEXT ANSWER ---
    next_answer = db.session.query(Answer).filter(
        Answer.participant_id == participant.id,
        Answer.study_id == study.id,
        Answer.status == 0,
        or_(
            Answer.result_id.in_(valid_result_ids),
            Answer.result_ai_id.in_(valid_ai_ids),
            Answer.result_chatbot_id.in_(valid_chatbot_ids),
            Answer.result_serp_id.in_(valid_serp_ids),
            Answer.result_ai_source_id.in_(valid_ai_source_ids),
            Answer.result_image_id.in_(valid_image_ids)
        )
    ).order_by(Answer.id).first()

    if not next_answer:
        # Load all assigned elements to correctly measure query limits!
        all_participant_answers = db.session.query(Answer).filter(
            Answer.participant_id == participant.id,
            Answer.study_id == study.id
        ).all()
        
        seen_queries = set()
        seen_items_count = 0
        first_question_id = study.questions[0].id if study.questions else None
        
        for ans in all_participant_answers:
            if ans.status in [1, 2] and first_question_id and ans.question_id == first_question_id: 
                seen_items_count += 1
            if ans.result_id and ans.result.query_id: seen_queries.add(ans.result.query_id)
            elif ans.result_ai_id and ans.result_ai.query_id: seen_queries.add(ans.result_ai.query_id)
            elif ans.result_chatbot_id and ans.result_chatbot.query_id: seen_queries.add(ans.result_chatbot.query_id)
            elif ans.result_serp_id and ans.result_serp.query_id: seen_queries.add(ans.result_serp.query_id)
            elif ans.result_ai_source_id and ans.result_ai_source.query_id: seen_queries.add(ans.result_ai_source.query_id)
            elif ans.result_image_id and ans.result_image.query_id: seen_queries.add(ans.result_image.query_id)
            
        limit_reached = False
        
        # 1. QUERY LIMIT PRÜFEN
        if study.group_by_query and study.limit_by_query:
            if study.max_queries_per_participant is not None and study.max_queries_per_participant > 0:
                if len(seen_queries) >= study.max_queries_per_participant: 
                    limit_reached = True

        # 2. ITEM LIMIT PRÜFEN
        if study.limit_per_participant:
            if study.max_results_per_participant is not None and study.max_queries_per_participant > 0:
                if seen_items_count >= study.max_results_per_participant: 
                    limit_reached = True
            
        if not limit_reached:
            # Berechne Restplatz für Items
            items_left = 99999
            if study.limit_per_participant and study.max_results_per_participant:
                items_left = study.max_results_per_participant - seen_items_count
                if items_left < 0: items_left = 0

            allowed_types = [t.strip().lower() for t in study.assessable_result_types_text.split(',')] if study.assessable_result_types_text else []
            res_types_map = {rt.name.strip().lower(): rt.id for rt in db.session.query(ResultType).all()}
            assigned_successfully = False

            if study.group_by_query and items_left > 0:
                available_queries = db.session.query(Query).filter(
                    Query.study_id == study.id,
                    ~Query.id.in_(seen_queries if seen_queries else [-1])
                ).all()
                
                if available_queries:
                    # 1. Berechne die Häufigkeit pro Query vorab (Besser für die Server-Performance!)
                    query_counts = {}
                    for q in available_queries:
                        count = db.session.query(Answer.participant_id).filter(
                            Answer.study_id == study.id,
                            or_(
                                Answer.result_id.in_(db.session.query(Result.id).filter_by(query_id=q.id)),
                                Answer.result_ai_id.in_(db.session.query(ResultAi.id).filter_by(query_id=q.id)),
                                Answer.result_chatbot_id.in_(db.session.query(ResultChatbot.id).filter_by(query_id=q.id)),
                                Answer.result_serp_id.in_(db.session.query(Serp.id).filter_by(query_id=q.id)),
                                Answer.result_ai_source_id.in_(db.session.query(ResultAiSource.id).filter_by(query_id=q.id)),
                                Answer.result_image_id.in_(db.session.query(ResultImage.id).filter_by(query_id=q.id))
                            )
                        ).distinct().count()
                        query_counts[q.id] = count

                    # 2. Echte Randomisierung: Mische die Liste zuerst mit roher Gewalt komplett durch
                    random.shuffle(available_queries)
                    
                    # 3. Balancierung: Sortiere nach der Häufigkeit
                    # (Da Python's Sort "stable" ist, bleiben gleich oft zugewiesene Queries perfekt zufällig gemischt!)
                    available_queries.sort(key=lambda q: query_counts[q.id])
                    
                    for candidate_query in available_queries:
                        locked_query = db.session.query(Query).filter_by(id=candidate_query.id).with_for_update(skip_locked=True).first()
                        if locked_query:
                            items_to_assign = []
                            
                            if 'organic' in allowed_types: 
                                q = db.session.query(Result).filter_by(query_id=locked_query.id)
                                if study.result_count: q = q.filter(Result.position <= study.result_count)
                                if ranges: q = q.filter(or_(*[and_(Result.position >= r.range_start, Result.position <= r.range_end) for r in ranges]))
                                if include_filters: q = q.filter(or_(*[Result.normalized_url.contains(clean_filter_string(f)) for f in include_filters]))
                                if exclude_filters: q = q.filter(and_(*[~Result.normalized_url.contains(clean_filter_string(f)) for f in exclude_filters]))
                                items_to_assign.extend(q.all())
                                
                            if 'ai overview' in allowed_types or 'ai_overview' in allowed_types: 
                                items_to_assign.extend(db.session.query(ResultAi).filter_by(query_id=locked_query.id).all())
                                
                            if 'chatbot' in allowed_types: 
                                items_to_assign.extend(db.session.query(ResultChatbot).filter_by(query_id=locked_query.id).all())
                                
                            if 'serp' in allowed_types: 
                                items_to_assign.extend(db.session.query(Serp).filter_by(query_id=locked_query.id).all())
                                
                            if 'ai_source' in allowed_types: 
                                q = db.session.query(ResultAiSource).filter_by(query_id=locked_query.id)
                                if study.result_count: q = q.filter(ResultAiSource.position <= study.result_count)
                                if ranges: q = q.filter(or_(*[and_(ResultAiSource.position >= r.range_start, ResultAiSource.position <= r.range_end) for r in ranges]))
                                items_to_assign.extend(q.all())
                                
                            if 'image result' in allowed_types or 'image' in allowed_types: 
                                q = db.session.query(ResultImage).filter_by(query_id=locked_query.id)
                                if study.result_count: q = q.filter(ResultImage.position <= study.result_count)
                                if ranges: q = q.filter(or_(*[and_(ResultImage.position >= r.range_start, ResultImage.position <= r.range_end) for r in ranges]))
                                items_to_assign.extend(q.all())
                            
                            # BALANCIERTE ZUWEISUNG (Kürzt die Liste, wenn das Item-Limit zuschlägt)
                            if items_to_assign:
                                if len(items_to_assign) > items_left:
                                    grouped = {}
                                    for t in items_to_assign:
                                        t_type = type(t).__name__
                                        if t_type not in grouped: grouped[t_type] = []
                                        grouped[t_type].append(t)
                                    
                                    for k in grouped: random.shuffle(grouped[k])
                                    
                                    balanced_items = []
                                    while len(balanced_items) < items_left:
                                        added = False
                                        keys = list(grouped.keys())
                                        random.shuffle(keys)
                                        for k in keys:
                                            if grouped[k] and len(balanced_items) < items_left:
                                                balanced_items.append(grouped[k].pop(0))
                                                added = True
                                        if not added: break
                                    
                                    items_to_assign = balanced_items
                                else:
                                    random.shuffle(items_to_assign)

                                for task in items_to_assign:
                                    task_type_text = "organic"
                                    if isinstance(task, ResultAi): task_type_text = "ai overview"
                                    elif isinstance(task, ResultChatbot): task_type_text = "chatbot"
                                    elif isinstance(task, Serp): task_type_text = "serp"
                                    elif isinstance(task, ResultAiSource): task_type_text = "ai_source"
                                    elif isinstance(task, ResultImage): task_type_text = "image"
                                    
                                    resolved_type_id = res_types_map.get(task_type_text, 1)
                                    for question in study.questions:
                                        ans = Answer(study_id=study.id, question_id=question.id, participant_id=participant.id, status=0, created_at=datetime.now(), resulttype=resolved_type_id, result_type_text=task_type_text)
                                        if isinstance(task, Result): ans.result = task
                                        elif isinstance(task, ResultAi): ans.result_ai = task
                                        elif isinstance(task, ResultChatbot): ans.result_chatbot = task
                                        elif isinstance(task, Serp): ans.result_serp = task
                                        elif isinstance(task, ResultAiSource): ans.result_ai_source = task
                                        elif isinstance(task, ResultImage): ans.result_image = task
                                        db.session.add(ans)
                                db.session.commit()
                                assigned_successfully = True
                                break
                            else: 
                                db.session.commit()
            
            else:
                if items_left > 0:
                    pools = {}
                    seen_res_ids = [r[0] for r in db.session.query(Answer.result_id).filter(Answer.participant_id == participant.id, Answer.result_id.isnot(None)).all()]
                    seen_ai_ids = [r[0] for r in db.session.query(Answer.result_ai_id).filter(Answer.participant_id == participant.id, Answer.result_ai_id.isnot(None)).all()]
                    seen_chat_ids = [r[0] for r in db.session.query(Answer.result_chatbot_id).filter(Answer.participant_id == participant.id, Answer.result_chatbot_id.isnot(None)).all()]
                    seen_serp_ids = [r[0] for r in db.session.query(Answer.result_serp_id).filter(Answer.participant_id == participant.id, Answer.result_serp_id.isnot(None)).all()]
                    seen_ai_source_ids = [r[0] for r in db.session.query(Answer.result_ai_source_id).filter(Answer.participant_id == participant.id, Answer.result_ai_source_id.isnot(None)).all()]
                    seen_image_ids = [r[0] for r in db.session.query(Answer.result_image_id).filter(Answer.participant_id == participant.id, Answer.result_image_id.isnot(None)).all()]
                    
                    if 'organic' in allowed_types: 
                        q = db.session.query(Result).filter(Result.study_id == study.id, ~Result.id.in_(seen_res_ids if seen_res_ids else [-1]))
                        if study.result_count: q = q.filter(Result.position <= study.result_count)
                        if ranges: q = q.filter(or_(*[and_(Result.position >= r.range_start, Result.position <= r.range_end) for r in ranges]))
                        if include_filters: q = q.filter(or_(*[Result.normalized_url.contains(clean_filter_string(f)) for f in include_filters]))
                        if exclude_filters: q = q.filter(and_(*[~Result.normalized_url.contains(clean_filter_string(f)) for f in exclude_filters]))
                        pools['organic'] = q.all()
                        
                    if 'ai overview' in allowed_types or 'ai_overview' in allowed_types: 
                        pools['ai'] = db.session.query(ResultAi).filter(ResultAi.study_id == study.id, ~ResultAi.id.in_(seen_ai_ids if seen_ai_ids else [-1])).all()
                        
                    if 'chatbot' in allowed_types: 
                        pools['chatbot'] = db.session.query(ResultChatbot).filter(ResultChatbot.study_id == study.id, ~ResultChatbot.id.in_(seen_chat_ids if seen_chat_ids else [-1])).all()
                        
                    if 'serp' in allowed_types: 
                        pools['serp'] = db.session.query(Serp).filter(Serp.study_id == study.id, ~Serp.id.in_(seen_serp_ids if seen_serp_ids else [-1])).all()
                        
                    if 'ai_source' in allowed_types: 
                        q = db.session.query(ResultAiSource).filter(ResultAiSource.study_id == study.id, ~ResultAiSource.id.in_(seen_ai_source_ids if seen_ai_source_ids else [-1]))
                        if study.result_count: q = q.filter(ResultAiSource.position <= study.result_count)
                        if ranges: q = q.filter(or_(*[and_(ResultAiSource.position >= r.range_start, ResultAiSource.position <= r.range_end) for r in ranges]))
                        pools['ai_source'] = q.all()
                        
                    if 'image result' in allowed_types or 'image' in allowed_types: 
                        q = db.session.query(ResultImage).filter(ResultImage.study_id == study.id, ~ResultImage.id.in_(seen_image_ids if seen_image_ids else [-1]))
                        if study.result_count: q = q.filter(ResultImage.position <= study.result_count)
                        if ranges: q = q.filter(or_(*[and_(ResultImage.position >= r.range_start, ResultImage.position <= r.range_end) for r in ranges]))
                        pools['image'] = q.all()
                    
                    all_pool_items = []
                    for p_name, items in pools.items(): all_pool_items.extend(items)
                    if all_pool_items:
                        counts = db.session.query(
                            func.coalesce(Answer.result_id, Answer.result_ai_id, Answer.result_chatbot_id, Answer.result_serp_id, Answer.result_ai_source_id, Answer.result_image_id).label('item_id'), 
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
                                elif isinstance(locked_task, ResultAiSource): task_type_text = "ai_source"
                                elif isinstance(locked_task, ResultImage): task_type_text = "image"
                                
                                resolved_type_id = res_types_map.get(task_type_text, 1)
                                for question in study.questions:
                                    ans = Answer(study_id=study.id, question_id=question.id, participant_id=participant.id, status=0, created_at=datetime.now(), resulttype=resolved_type_id, result_type_text=task_type_text)
                                    if isinstance(locked_task, Result): ans.result = locked_task
                                    elif isinstance(locked_task, ResultAi): ans.result_ai = locked_task
                                    elif isinstance(locked_task, ResultChatbot): ans.result_chatbot = locked_task
                                    elif isinstance(locked_task, Serp): ans.result_serp = locked_task
                                    elif isinstance(locked_task, ResultAiSource): ans.result_ai_source = locked_task
                                    elif isinstance(locked_task, ResultImage): ans.result_image = locked_task
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
            
            if task_item.normalized_url:
                if study.global_duplicate_filtering:
                    # GLOBALE SPERRE: Ignoriert die Query, sucht in der gesamten Studie
                    duplicates = Result.query.filter(
                        Result.study_id == study_id,
                        Result.normalized_url == task_item.normalized_url, 
                        Result.id != task_item.id
                    ).all()
                else:
                    # LOKALE SPERRE (Standard): Filtert nur innerhalb derselben Query
                    duplicates = Result.query.filter(
                        Result.study_id == study_id,
                        Result.query_id == task_item.query_id,
                        Result.normalized_url == task_item.normalized_url, 
                        Result.id != task_item.id
                    ).all()
                    
                all_duplicate_result_ids = {d.id for d in duplicates}
                
            has_source = (task_item.sources and task_item.sources[0] and task_item.sources[0].file_path)
            if not has_source and not study.assess_failed and not study.live_link_mode:
                target_skip_ids = all_duplicate_result_ids.union({task_item.id})
                if target_skip_ids:
                    answers_to_skip = db.session.query(Answer).filter(
                        Answer.participant_id == participant.id, 
                        Answer.result_id.in_(target_skip_ids)
                    ).all()
                    for answer in answers_to_skip: 
                        answer.status = 2
                        answer.created_at = datetime.now()
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
            if not task_item.file_path and not study.assess_failed and not study.live_link_mode:
                next_answer.status = 2
                next_answer.created_at = datetime.now()
                db.session.commit()
                return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))
            answers_for_item = db.session.query(Answer).filter(Answer.result_serp_id == task_item.id, Answer.participant_id == participant.id).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = answers_for_item        
            
    elif next_answer.result_ai_source_id:
        task_type = 'result_ai_source'
        task_item = db.session.get(ResultAiSource, next_answer.result_ai_source_id)
        if task_item:
            if task_item.progress != 1 and not study.assess_failed and not study.live_link_mode:
                next_answer.status = 2
                next_answer.created_at = datetime.now()
                db.session.commit()
                return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))
            answers_for_item = db.session.query(Answer).filter(Answer.result_ai_source_id == task_item.id, Answer.participant_id == participant.id).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = answers_for_item            
            
    elif next_answer.result_image_id:
        task_type = 'result_image'
        task_item = db.session.query(ResultImage).options(joinedload(ResultImage.source)).get(next_answer.result_image_id)
        if task_item:
            if task_item.progress != 1 and not study.assess_failed and not study.live_link_mode:
                next_answer.status = 2
                next_answer.created_at = datetime.now()
                db.session.commit()
                return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))
            answers_for_item = db.session.query(Answer).filter(Answer.result_image_id == task_item.id, Answer.participant_id == participant.id).join(Question).options(joinedload(Answer.question)).order_by(Question.position).all()
            answers_to_update = answers_for_item
            
    if not task_item:
        next_answer.status = 2; db.session.commit()
        return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))

    questions_count = len(study.questions) or 1
    query_info_text = None
    
    if study.group_by_query:
        active_query_id = None
        if task_item:
            if hasattr(task_item, 'query_id') and task_item.query_id: active_query_id = task_item.query_id
            elif hasattr(task_item, 'query_') and task_item.query_: active_query_id = task_item.query_.id
            elif hasattr(task_item, 'query') and task_item.query: active_query_id = task_item.query.id
                
        all_ans = db.session.query(Answer).filter(Answer.participant_id == participant.id, Answer.study_id == study.id).all()
        seen_queries = set()
        query_closed = 0
        query_open = 0
        
        for ans in all_ans:
            q_id = None
            if ans.result_id and ans.result.query_id: q_id = ans.result.query_id
            elif ans.result_ai_id and ans.result_ai.query_id: q_id = ans.result_ai.query_id
            elif ans.result_chatbot_id and ans.result_chatbot.query_id: q_id = ans.result_chatbot.query_id
            elif ans.result_serp_id and ans.result_serp.query_id: q_id = ans.result_serp.query_id
            elif ans.result_ai_source_id and ans.result_ai_source.query_id: q_id = ans.result_ai_source.query_id
            elif ans.result_image_id and ans.result_image.query_id: q_id = ans.result_image.query_id
            
            if q_id:
                seen_queries.add(q_id)
                # Nur Items der AKTUELLEN Query für den Balken zählen
                if q_id == active_query_id:
                    if ans.status in [1, 2]: query_closed += 1
                    elif ans.status == 0: query_open += 1
                        
        closed_tasks_count = query_closed // questions_count
        open_tasks_count = query_open // questions_count
        all_tasks_count = closed_tasks_count + open_tasks_count
        if all_tasks_count == 0: all_tasks_count = 1
        
        pct = round((closed_tasks_count / all_tasks_count) * 100) if all_tasks_count > 0 else 0
        if pct > 100: pct = 100
        
        # Text generieren (-1 oder 0 = unendlich)
        current_q = len(seen_queries) if len(seen_queries) > 0 else 1
        
        if study.limit_by_query and study.max_queries_per_participant is not None and study.max_queries_per_participant > 0:
            max_q = study.max_queries_per_participant
            if current_q > max_q: current_q = max_q
            query_info_text = f"Working on Search Query {current_q} of {max_q}"
        else:
            query_info_text = f"Working on Search Query {current_q}"
            
    else:
        closed_tasks_count = db.session.query(Answer.id).filter(Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status.in_([1, 2])).count() // questions_count
        open_tasks_count = db.session.query(Answer.id).filter(Answer.participant_id == participant.id, Answer.study_id == study.id, Answer.status == 0).count() // questions_count

        if study.limit_per_participant and study.max_results_per_participant is not None and study.max_results_per_participant != -1:
            all_tasks_count = study.max_results_per_participant
            if closed_tasks_count > all_tasks_count: closed_tasks_count = all_tasks_count
        else:
            all_tasks_count = closed_tasks_count + open_tasks_count
            
        if all_tasks_count == 0: all_tasks_count = 1

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
                rt_map = {'result': 1, 'result_ai': 2, 'result_chatbot': 4, 'serp': 5, 'result_ai_source': 6, 'result_image': 7}
                for answer in answers_to_update:
                    answer.value = submitted_values.get(answer.question_id, ''); answer.status = 1; answer.created_at = datetime.now(); answer.resulttype = rt_map.get(task_type, 1)
                db.session.commit()
                return redirect(url_for('assessment', participant_id=participant_id, study_id=study_id))
            
            # FEHLERBEHEBUNG: query_info_text übergeben
            return render_template('assessments/assessment.html', form=form, answers=answers_for_item, task_item=task_item, task_type=task_type, all=all_tasks_count, closed=closed_tasks_count, pct=pct, show_urls=study.show_urls, study=study, errors=errors, submitted_data=request.form, query_info_text=query_info_text)

    # FEHLERBEHEBUNG: query_info_text übergeben
    return render_template('assessments/assessment.html', form=form, answers=answers_for_item, task_item=task_item, task_type=task_type, all=all_tasks_count, closed=closed_tasks_count, pct=pct, show_urls=study.show_urls, study=study, errors={}, submitted_data={}, query_info_text=query_info_text)

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
        submitted = {
            q['id']: request.form.getlist(q['id']) if q['type'] == 'multiple_choice' else request.form.get(q['id'], '') 
            for q in questions if q.get('type') != 'heading'
        }        
        ans_dict = json.loads(participant.pre_survey_answers if survey_type == 'pre' else participant.post_survey_answers) if (participant.pre_survey_answers if survey_type == 'pre' else participant.post_survey_answers) else {}
        ans_dict[str(study.id)] = submitted
        if survey_type == 'pre': participant.pre_survey_answers = json.dumps(ans_dict)
        else: participant.post_survey_answers = json.dumps(ans_dict)
        db.session.commit()
        return redirect(url_for('assessment', participant_id=participant.id, study_id=study.id))
    return render_template('surveys/survey.html', title=f"{survey_type.capitalize()}-Survey", questions=questions, study=study)

@app.route('/study/<study_id>/preview/survey/<survey_type>')
def preview_survey(study_id, survey_type):
    study = Study.query.get_or_404(study_id)
    json_data = study.pre_survey_json if survey_type == 'pre' else study.post_survey_json
    questions = json.loads(json_data) if json_data else []
    
    return render_template('surveys/survey.html', 
                           title=f"[PRETEST VORSCHAU] {survey_type.capitalize()}-Survey", 
                           questions=questions, 
                           study=study, 
                           is_preview=True)

@app.route('/study/<study_id>/preview/assessment')
def preview_assessment(study_id):
    study = Study.query.get_or_404(study_id)
    
    task_item = Result.query.filter_by(study_id=study.id).first()
    task_type = 'result'
    if not task_item:
        task_item = ResultAi.query.filter_by(study_id=study.id).first()
        task_type = 'result_ai'
    if not task_item:
        task_item = ResultChatbot.query.filter_by(study_id=study.id).first()
        task_type = 'result_chatbot'
    if not task_item:
        task_item = Serp.query.filter_by(study_id=study.id).first()
        task_type = 'serp'
    if not task_item:
        task_item = ResultAiSource.query.filter_by(study_id=study.id).first()
        task_type = 'result_ai_source'
    if not task_item:
        task_item = ResultImage.query.filter_by(study_id=study.id).first()
        task_type = 'result_image'
        
    if not task_item:
        flash("Für die Vorschau des Assessments müssen zuerst Daten hochgeladen werden.", "warning")
        return redirect(request.referrer or '/')

    dummy_answers = []
    for q in study.questions:
        dummy_ans = Answer(question=q, question_id=q.id)
        dummy_answers.append(dummy_ans)
        
    form = FlaskForm()
    
    return render_template('assessments/assessment.html', 
                           form=form, answers=dummy_answers, 
                           task_item=task_item, task_type=task_type, 
                           all=1, closed=0, pct=0, 
                           show_urls=study.show_urls, study=study, 
                           errors={}, submitted_data={},
                           is_preview=True)

@app.route('/study/<study_id>/preview/welcome')
def preview_welcome(study_id):
    study = Study.query.get_or_404(study_id)
    
    # Render the welcome page without a real participant and prevent redirecting
    return render_template('surveys/welcome.html', 
                           study=study, 
                           participant=None, 
                           next_url="#", 
                           is_preview=True)

@app.route('/study/<study_id>/preview/completed')
def preview_completed(study_id):
    study = Study.query.get_or_404(study_id)
    
    # Simulate a 100% finished study to trigger the completion text
    return render_template('assessments/assessments.html', 
                           study=study, 
                           participant=None,
                           answers_all=1, 
                           answers_closed=1, 
                           pct=100,
                           is_preview=True)