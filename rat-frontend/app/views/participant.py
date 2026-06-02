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

    study = Study.query.get_or_404(study_id)
    
    max_id = db.session.query(func.max(Participant.id)).scalar() or 0
    participant = Participant(
        name='user' + str(max_id + 1),
        created_at=datetime.now(),
        password=random.randint(1000, 9999)
    )
    participant.studies.append(study)
    db.session.add(participant)

    # --- TASK ASSIGNMENT BLOCK (participant.py) ---
    selected_types = [t.strip().lower() for t in study.assessable_result_types_text.split(',')] if study.assessable_result_types_text else []
        
    # Get limits

    max_items = study.max_results_per_participant if (study.limit_per_participant and study.max_results_per_participant) else 99999

    # Memory Safe Limit: Only pull what we reasonably need for shuffling (e.g., 3x the max_items)
    fetch_limit = max_items * 3 

    all_available_tasks = []

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

        # Apply Range and URL filters
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

        # CHANGED: Append to master list
        org_tasks = org_q.order_by(Result.assignment_count.asc()).limit(fetch_limit).all()
        all_available_tasks.extend(org_tasks)

        # 2. Fetch AI Overviews
        ai_tasks = db.session.query(ResultAi).filter(
            ResultAi.study_id == study.id, ResultAi.result_type_text.in_(selected_types)
        ).order_by(ResultAi.assignment_count.asc()).limit(fetch_limit).all()
        all_available_tasks.extend(ai_tasks)

        # 3. Fetch Chatbots
        chat_tasks = db.session.query(ResultChatbot).filter(
            ResultChatbot.study_id == study.id, ResultChatbot.result_type_text.in_(selected_types)
        ).order_by(ResultChatbot.assignment_count.asc()).limit(fetch_limit).all()
        all_available_tasks.extend(chat_tasks)
            
        # 4. Fetch SERPs
        if "serp" in selected_types:
            serp_tasks = db.session.query(Serp).filter(
                Serp.study_id == study.id
            ).order_by(Serp.assignment_count.asc()).limit(fetch_limit).all()
            all_available_tasks.extend(serp_tasks)

    final_tasks = []
    
    # Sort EVERYTHING by assignment count so the least-rated items are always first
    all_available_tasks.sort(key=lambda x: (x.assignment_count or 0, random.random()))
    
    # ---------------------------------------------------------
     # MODE A: QUERY PRIORITY QUEUE (Limit by Query & Items)
    # ---------------------------------------------------------
    db_query_limit = getattr(study, 'max_queries_per_participant', -1)
    
    if db_query_limit != -1:
        max_queries = db_query_limit if db_query_limit > 0 else 99999
        
        tasks_by_query = {}
        for task in all_available_tasks:
            q_obj = getattr(task, 'query_', None)
            if not q_obj: continue
            
            if q_obj not in tasks_by_query:
                tasks_by_query[q_obj] = {'org': [], 'ai': [], 'chat': [], 'serp': []}
            
            if isinstance(task, Result): tasks_by_query[q_obj]['org'].append(task)
            elif isinstance(task, ResultAi): tasks_by_query[q_obj]['ai'].append(task)
            elif isinstance(task, ResultChatbot): tasks_by_query[q_obj]['chat'].append(task)
            elif isinstance(task, Serp): tasks_by_query[q_obj]['serp'].append(task)

        # Sort queries by assignment count (Least assigned first)
        sorted_queries = sorted(list(tasks_by_query.keys()), key=lambda q: (q.assignment_count or 0, random.random()))

        added_queries_count = 0
        
        for q_obj in sorted_queries:
            if added_queries_count >= max_queries: break
            
            q_cluster = tasks_by_query[q_obj]
            
            # 1. Nimm ALLE Elemente dieser Query (über alle Suchmaschinen hinweg!)
            cluster_tasks = []
            cluster_tasks.extend(q_cluster['ai'])
            cluster_tasks.extend(q_cluster['serp'])
            cluster_tasks.extend(q_cluster['chat'])
            cluster_tasks.extend(q_cluster['org'])
            
            if not cluster_tasks: continue

            # WICHTIG: Die Query wird nur als GANZES Paket zugewiesen.
            # Wenn das Hinzufügen dieser Query das Item-Limit des Teilnehmers sprengen würde,
            # weisen wir sie nicht mehr zu (außer es ist seine allererste Query).
            if len(final_tasks) > 0 and (len(final_tasks) + len(cluster_tasks) > max_items):
                break 
                
            # 2. RANDOMISIERUNG (Gegen Reihenfolge-Bias)
            # Mischt Google, Bing, SERPs und organische Ergebnisse dieser Query bunt durch.
            random.shuffle(cluster_tasks)
            
            final_tasks.extend(cluster_tasks)
            added_queries_count += 1
            
            # Increment the Query Priority Counter
            if getattr(q_obj, 'assignment_count', None) is None:
                q_obj.assignment_count = 0
            q_obj.assignment_count += 1

    # ---------------------------------------------------------
    # MODE B: STRATIFIED RANDOM (Limit by Items Only)
    # ---------------------------------------------------------
    else:
        # Group the already-sorted items into pools
        pools = {'org': [], 'ai': [], 'chat': [], 'serp': []}
        for task in all_available_tasks:
            if isinstance(task, Result): pools['org'].append(task)
            elif isinstance(task, ResultAi): pools['ai'].append(task)
            elif isinstance(task, ResultChatbot): pools['chat'].append(task)
            elif isinstance(task, Serp): pools['serp'].append(task)

        while len(final_tasks) < max_items:
            added = 0
            for key in ['org', 'ai', 'chat', 'serp']:
                if pools[key]:
                    # Pulls the absolute lowest assignment_count item of this type
                    final_tasks.append(pools[key].pop(0))
                    added += 1
                if len(final_tasks) >= max_items: break
            if added == 0: break
            
        # RANDOMIZE the presentation order so it isn't strictly Org -> AI -> Chat -> Serp
        random.shuffle(final_tasks)

    # --- ANSWER CREATION & RESULTTYPE MAPPING ---
    res_types_map = {rt.name.strip().lower(): rt.id for rt in db.session.query(ResultType).all()}

    for task in final_tasks:
        # Resolve the string name
        task_type_text = "serp"
        if isinstance(task, Result): task_type_text = getattr(task, 'result_type_text', 'organic')
        elif isinstance(task, ResultAi): task_type_text = getattr(task, 'result_type_text', 'ai overview')
        elif isinstance(task, ResultChatbot): task_type_text = getattr(task, 'result_type_text', 'chatbot')

        task_type_text = str(task_type_text).strip().lower()
        # Resolve the database ID
        resolved_type_id = res_types_map.get(task_type_text, 1)

        # Increment the item assignment counter ONCE per task (not per question)
        if getattr(task, 'assignment_count', None) is None: 
            task.assignment_count = 0
        task.assignment_count += 1

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