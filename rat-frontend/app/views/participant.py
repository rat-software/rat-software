from .. import app, db
from app.models import (Study, Participant, Answer, Result, Question, ResultAi, 
                        ResultChatbot, ResultSource, Serp, RangeStudy, ResultType)
from ..forms import JoinForm, ParticipantLogInForm, ConfirmationForm
from flask import render_template, flash, redirect, url_for, request, send_file
from datetime import datetime
from flask_login import logout_user
import random
from io import BytesIO
import sqlalchemy
from sqlalchemy import func, update, or_, and_, literal_column
from ..helpers import clean_filter_string

from datetime import timedelta


@app.route('/study/<id>/participants')
def participants(id):
    study = Study.query.get_or_404(id)
    info = []
    questions_count = len(study.questions)

    for participant in study.participants:
        query = db.session.query(Answer).filter(
            Answer.participant == participant,
            Answer.study == study
        )
        
        all_count = (query.count() // questions_count) if questions_count > 0 else 0
        open_count = (query.filter(Answer.status == 0).count() // questions_count) if questions_count > 0 else 0
        closed_count = (query.filter(Answer.status == 1).count() // questions_count) if questions_count > 0 else 0
        skipped_count = (query.filter(Answer.status == 2).count() // questions_count) if questions_count > 0 else 0

        info.append([participant, all_count, open_count, closed_count, skipped_count])

    return render_template('participants/participants.html', study=study, info=info)


@app.route('/participant/<id>', methods=["GET", "POST"])
def participant(id):
    logout_user()
    participant = Participant.query.get_or_404(id)
    base = request.url_root
    form = ConfirmationForm()
    
    db.session.execute(sqlalchemy.sql.text(
        "UPDATE answer SET source_status_code = source.status_code "
        "FROM source JOIN result_source ON source.id = result_source.source "
        "WHERE answer.result = result_source.result AND answer.participant = :p_id"
    ), {'p_id': participant.id})
    db.session.commit()
    
    info = []
    
    for study in participant.studies:
        questions_count = len(study.questions)
        if questions_count == 0:
            info.append([study.id, 0, 0, 0, 0])
            continue

        organic_q = db.session.query(Answer.result_id).filter(
            Answer.participant_id == participant.id,
            Answer.study_id == study.id,
            Answer.status == 0,
            Answer.result_id.isnot(None)
        ).join(Result).join(Result.source_associations)
        
        if study.assess_failed:
            organic_q = organic_q.filter(or_(ResultSource.progress == 1, ResultSource.progress == -1))
        else:
            organic_q = organic_q.filter(ResultSource.progress == 1)
            
        valid_open_organic_query = organic_q.distinct()
        
        ranges = RangeStudy.query.filter_by(study=study.id).all()
        if ranges:
            range_filters = [and_(Result.position >= r.range_start, Result.position <= r.range_end) for r in ranges]
            valid_open_organic_query = valid_open_organic_query.filter(or_(*range_filters))
        
        include_filters = [f.url for f in study.study_url_filters if f.include and f.url]
        if include_filters:
            valid_open_organic_query = valid_open_organic_query.filter(or_(*[Result.normalized_url.contains(clean_filter_string(f)) for f in include_filters]))

        exclude_filters = [f.url for f in study.study_url_filters if f.exclude and f.url]
        if exclude_filters:
            valid_open_organic_query = valid_open_organic_query.filter(and_(*[~Result.normalized_url.contains(clean_filter_string(f)) for f in exclude_filters]))
            
        open_organic_count = valid_open_organic_query.count()

        base_query = db.session.query(Answer).filter(
            Answer.participant_id == participant.id,
            Answer.study_id == study.id
        )
        
        open_ai_count = base_query.filter(
            Answer.status == 0, Answer.result_ai_id.isnot(None)
        ).distinct(Answer.result_ai_id).count()
        
        open_chatbot_count = base_query.filter(
            Answer.status == 0, Answer.result_chatbot_id.isnot(None)
        ).distinct(Answer.result_chatbot_id).count()
        
        open_serp_count = base_query.filter(
            Answer.status == 0, Answer.result_serp_id.isnot(None)
        ).distinct(Answer.result_serp_id).count()

        open_count = open_organic_count + open_ai_count + open_chatbot_count + open_serp_count
        
        closed_count = (base_query.filter(Answer.status == 1).count() // questions_count)
        skipped_count = (base_query.filter(Answer.status == 2).count() // questions_count)

        all_count = open_count + closed_count + skipped_count

        info.append([study.id, all_count, open_count, closed_count, skipped_count])

    if request.method == 'POST':
        if 'download' in request.form:
            buffer = BytesIO()
            return_url = base + "resume/" + str(participant.id) + '/' + str(participant.password)
            text = 'Username: %s\nCode: %d\nReturn URL: %s' % (participant.name, participant.password, return_url)
            buffer.write(text.encode('utf-8'))
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name='RAT_return.txt', mimetype='text/csv')

    return render_template('participants/participant.html',
                           participant=participant,
                           info=info,
                           base=base,
                           form=form)


@app.route('/study/<study_id>/participant/new', methods=["GET", "POST"])
@app.route('/join/<study_id>', methods=["GET", "POST"])
def new_participant(study_id):
    logout_user()
    form = JoinForm()
    if not form.is_submitted() or not form.new.data:
        if form.is_submitted() and form.returning.data:
            return redirect(url_for('returning_participant', study_id=study_id))
        return render_template('participants/join.html', form=form)

    # ---------------------------------------------------------
    # 1. PESSIMISTIC LOCKING
    # Secures the row in the database to prevent concurrent 
    # thread overlap or race conditions during allocation.
    # ---------------------------------------------------------
    study = db.session.query(Study).with_for_update().get_or_404(study_id)
    
    max_id = db.session.query(func.max(Participant.id)).scalar() or 0
    participant = Participant(
        name='user' + str(max_id + 1),
        created_at=datetime.now(),
        password=random.randint(1000, 9999)
    )
    participant.studies.append(study)
    db.session.add(participant)

    # --- TASK ASSIGNMENT BLOCK ---
    selected_types = [t.strip().lower() for t in study.assessable_result_types_text.split(',')] if study.assessable_result_types_text else []
        
    max_items = study.max_results_per_participant if (study.limit_per_participant and study.max_results_per_participant) else 99999
    
    # Memory optimization guard: fetch only what is reasonably required for balancing/shuffling
    fetch_limit = 99999
    all_available_tasks = []

    # PRÜFUNG: Dürfen wir ein Limit setzen oder machen wir die Gruppierung kaputt?
    # Wenn limit_by_query aktiv ist, laden wir ALLES, um die Queries nicht zu zerschneiden.
    apply_limit = not (study.limit_by_query and study.max_queries_per_participant != -1)

    if selected_types:
        # 1. Fetch Organic Results
        org_q = db.session.query(Result).join(Result.source_associations).filter(
            Result.study_id == study.id,
            Result.result_type_text.in_(selected_types)
        )
        if study.assess_failed:
            org_q = org_q.filter(or_(ResultSource.progress == 1, ResultSource.progress == -1))
        else:
            org_q = org_q.filter(ResultSource.progress == 1)

        ranges = RangeStudy.query.filter_by(study=study.id).all()
        if ranges:
            range_filters = [and_(Result.position >= r.range_start, Result.position <= r.range_end) for r in ranges]
            org_q = org_q.filter(or_(*range_filters))
            
        include_filters = [f.url for f in study.study_url_filters if f.include and f.url]
        if include_filters:
            org_q = org_q.filter(or_(*[Result.normalized_url.contains(clean_filter_string(f)) for f in include_filters]))

        exclude_filters = [f.url for f in study.study_url_filters if f.exclude and f.url]
        if exclude_filters:
            org_q = org_q.filter(and_(*[~Result.normalized_url.contains(clean_filter_string(f)) for f in exclude_filters]))

        # Hier greift die Logik für org_tasks
        org_tasks = org_q.limit(fetch_limit).all() if apply_limit else org_q.all()
        all_available_tasks.extend(org_tasks)

        # 2. Fetch AI Overviews
        ai_q = db.session.query(ResultAi).filter(
            ResultAi.study_id == study.id, ResultAi.result_type_text.in_(selected_types)
        )
        ai_tasks = ai_q.limit(fetch_limit).all() if apply_limit else ai_q.all()
        all_available_tasks.extend(ai_tasks)

        # 3. Fetch Chatbots
        chat_q = db.session.query(ResultChatbot).filter(
            ResultChatbot.study_id == study.id, ResultChatbot.result_type_text.in_(selected_types)
        )
        chat_tasks = chat_q.limit(fetch_limit).all() if apply_limit else chat_q.all()
        all_available_tasks.extend(chat_tasks)
            
        # 4. Fetch SERPs (Search Engine Result Pages)
        if "serp" in selected_types:
            serp_q = db.session.query(Serp).filter(Serp.study_id == study.id)
            serp_tasks = serp_q.limit(fetch_limit).all() if apply_limit else serp_q.all()
            all_available_tasks.extend(serp_tasks)

    # ---------------------------------------------------------
    # 2. DYNAMIC LIVE-SCORE CALCULATION
    # Dynamically reads the 'Answer' table to calculate a live metric.
    # Includes finished submissions (status=1) and highly active 
    # ongoing sessions (status=0, created within the last 45 mins).
    # ---------------------------------------------------------
    active_timeout = datetime.now() - timedelta(minutes=45)
    item_scores = {'result': {}, 'result_ai': {}, 'result_chatbot': {}, 'serp': {}}
    
    def fetch_live_scores(column_ref):
        return db.session.query(column_ref, func.count(Answer.id)).filter(
            Answer.study_id == study.id,
            column_ref.isnot(None),
            # Nur abgeschlossene oder explizit geskippte Items zählen als "belegt"
            Answer.status.in_([1, 2]) 
        ).group_by(column_ref).all()

    for r_id, score in fetch_live_scores(Answer.result_id): item_scores['result'][r_id] = score
    for r_id, score in fetch_live_scores(Answer.result_ai_id): item_scores['result_ai'][r_id] = score
    for r_id, score in fetch_live_scores(Answer.result_chatbot_id): item_scores['result_chatbot'][r_id] = score
    for r_id, score in fetch_live_scores(Answer.result_serp_id): item_scores['serp'][r_id] = score

    def get_live_score(task):
        if isinstance(task, Result): return item_scores['result'].get(task.id, 0)
        elif isinstance(task, ResultAi): return item_scores['result_ai'].get(task.id, 0)
        elif isinstance(task, ResultChatbot): return item_scores['result_chatbot'].get(task.id, 0)
        elif isinstance(task, Serp): return item_scores['serp'].get(task.id, 0)
        return 0

    # Sort all components globally by their calculated live score (least-reviewed items first)
    all_available_tasks.sort(key=lambda x: (get_live_score(x), random.random()))
    
    final_tasks = all_available_tasks[:max_items]
    
    # ---------------------------------------------------------
    # MODE A: QUERY PRIORITY QUEUE (Group items tightly by search queries)
    # ---------------------------------------------------------
    db_query_limit = study.max_queries_per_participant

    if db_query_limit is not None and db_query_limit != -1:
        max_queries = db_query_limit if db_query_limit > 0 else 99999
        tasks_by_query = {}
        
        # Structure elements into object pools mapped by their parent query
        for task in all_available_tasks:
            q_obj = getattr(task, 'query_', None)
            if not q_obj: continue
            if q_obj not in tasks_by_query: tasks_by_query[q_obj] = {'org': [], 'ai': [], 'chat': [], 'serp': []}
            
            if isinstance(task, Result): tasks_by_query[q_obj]['org'].append(task)
            elif isinstance(task, ResultAi): tasks_by_query[q_obj]['ai'].append(task)
            elif isinstance(task, ResultChatbot): tasks_by_query[q_obj]['chat'].append(task)
            elif isinstance(task, Serp): tasks_by_query[q_obj]['serp'].append(task)

        # Aggregate individual item scores to map an absolute query-level live score
        query_scores = {}
        for q_obj, clusters in tasks_by_query.items():
            query_scores[q_obj] = sum(get_live_score(t) for group in clusters.values() for t in group)

        # Base sorting: prioritize queries with the lowest accumulated score
        sorted_queries = sorted(list(tasks_by_query.keys()), key=lambda q: query_scores.get(q, 0))
        
        # --- ADAPTIVE CANDIDATE POOL MECHANISM ---
        # Select twice the amount of needed queries, capped safely at the maximum available count
        pool_size = min(max_queries * 2, len(sorted_queries))
        candidate_pool = sorted_queries[:pool_size]
        
        # Randomly sample the target number of queries from the highest priority candidate pool.
        # This significantly decreases the risk of priming effects with related sequential tasks.
        chosen_queries = random.sample(candidate_pool, min(len(candidate_pool), max_queries))
        # -----------------------------------------
        
        added_queries_count = 0
        
        # Iterate over our random, prioritized subset
        for q_obj in chosen_queries:
            if added_queries_count >= max_queries: break
            q_cluster = tasks_by_query[q_obj]
            
            cluster_tasks = q_cluster['ai'] + q_cluster['serp'] + q_cluster['chat'] + q_cluster['org']
            if not cluster_tasks: continue

            # Strict guard check for the total participant item workload capacity
            if len(final_tasks) > 0 and (len(final_tasks) + len(cluster_tasks) > max_items): break 
                
            # Randomize intra-query item sequences to completely eliminate layout or engine bias
            random.shuffle(cluster_tasks)
            final_tasks.extend(cluster_tasks)
            added_queries_count += 1

    # ---------------------------------------------------------
    # MODE B: STRATIFIED RANDOM (No query grouping, balance items directly)
    # ---------------------------------------------------------
    else:
        pools = {'org': [], 'ai': [], 'chat': [], 'serp': []}
        for task in all_available_tasks:
            if isinstance(task, Result): pools['org'].append(task)
            elif isinstance(task, ResultAi): pools['ai'].append(task)
            elif isinstance(task, ResultChatbot): pools['chat'].append(task)
            elif isinstance(task, Serp): pools['serp'].append(task)

        # Distribute workload equitably across available data domains until max_items is satisfied
        while len(final_tasks) < max_items:
            added = 0
            for key in ['org', 'ai', 'chat', 'serp']:
                if pools[key]:
                    final_tasks.append(pools[key].pop(0))
                    added += 1
                if len(final_tasks) >= max_items: break
            if added == 0: break
            
        random.shuffle(final_tasks)

    # --- ANSWER CREATION & RESULTTYPE MAPPING ---
    res_types_map = {rt.name.strip().lower(): rt.id for rt in db.session.query(ResultType).all()}

    for task in final_tasks:
        task_type_text = "serp"
        if isinstance(task, Result): task_type_text = getattr(task, 'result_type_text', 'organic')
        elif isinstance(task, ResultAi): task_type_text = getattr(task, 'result_type_text', 'ai overview')
        elif isinstance(task, ResultChatbot): task_type_text = getattr(task, 'result_type_text', 'chatbot')

        task_type_text = str(task_type_text).strip().lower()
        resolved_type_id = res_types_map.get(task_type_text, 1)

        # Legacy Counter: Kept active for passive administrative reporting dashboards
        if getattr(task, 'assignment_count', None) is None: task.assignment_count = 0
        task.assignment_count += 1

        # Generate persistent, blank assessment records for each linked survey question
        for question in study.questions:
            answer = Answer(
                study_id=study.id,
                question_id=question.id,
                participant_id=participant.id,
                status=0,
                created_at=datetime.now(),
                resulttype=resolved_type_id,
                result_type_text=task_type_text
            )
            
            if isinstance(task, Result): answer.result = task
            elif isinstance(task, ResultAi): answer.result_ai = task
            elif isinstance(task, ResultChatbot): answer.result_chatbot = task
            elif isinstance(task, Serp): answer.result_serp = task
                
            db.session.add(answer)

    # Committing implicitly breaks the pessimistic with_for_update() database lock,
    # clearing the gateway for the next user transaction.
    db.session.commit()
    return redirect(url_for('participant', id=participant.id))

@app.route('/study/<study_id>/participant/returning', methods=["GET", "POST"])
@app.route('/returning/<study_id>', methods=["GET", "POST"])
def returning_participant(study_id):
    logout_user()
    form = ParticipantLogInForm()

    if form.is_submitted():
        participant = Participant.query.filter(Participant.name == form.username.data).first()

        if participant and int(participant.password) == int(form.password.data):
            study = Study.query.get(study_id)
            if study not in participant.studies:
                participant.studies.append(study)
                db.session.commit()

            flash('Welcome back, '+ participant.name, 'success')
            return redirect(url_for('assessments', participant_id=participant.id, study_id=study.id))
        elif participant:
            flash('Code is incorrect', 'danger')
        else:
            flash('Username does not exist.', 'danger')

    return render_template('participants/returning.html',
                           form=form)


@app.route('/participant/<id>/<code>/resume')
@app.route('/resume/<id>/<code>')
def resume(id, code):
    logout_user()
    participant = Participant.query.get(id)
    if participant and int(participant.password) == int(code):
        flash('Welcome back!', 'success')
        return redirect(url_for('participant', id=id))
    else:
        flash('Code invalid.', 'danger')
        return redirect(url_for('security.login'))


@app.route('/participant/<id>/delete', methods=["GET", "POST"])
def delete_participant(id):
    logout_user()
    participant = Participant.query.get(id)
    
    if participant:
        Answer.query.filter_by(participant_id=id).delete()
        db.session.delete(participant)
        db.session.commit()
        flash('Participant deleted', 'success')
    else:
        flash('Participant not found', 'danger')
        
    return redirect(url_for('dashboard'))