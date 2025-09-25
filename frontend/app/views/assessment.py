from .. import app, db
from ..models import Study, Participant, Answer, Question, Result, StudyURLFilter, ResultAi, ResultChatbot, Source, ResultSource
from flask import render_template, flash, redirect, url_for, request
from flask_login import logout_user
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_, and_
from flask_wtf import FlaskForm
from urllib.parse import urlparse

def clean_filter_string(url_filter: str) -> str:
    # ... (function is unchanged)
    try:
        if '://' not in url_filter:
            url_filter = 'http://' + url_filter
        netloc = urlparse(url_filter).netloc.lower()
        if netloc.startswith('www.'):
            return netloc[4:]
        return netloc
    except:
        return url_filter.lower()

@app.route('/<study_id>/participant/<participant_id>/assessments')
def assessments(participant_id, study_id):
    logout_user()
    participant = Participant.query.get_or_404(participant_id)
    study = Study.query.get_or_404(study_id)

    base_query = db.session.query(Answer).filter(
        Answer.participant_id == participant.id,
        Answer.study_id == study.id
    )

    open_organic_query = base_query.join(Result).filter(
        Answer.status == 0,
        Answer.result_id.isnot(None),
        Answer.source_status_code == 200,
        Result.normalized_url.isnot(None), 
        Result.normalized_url != ""
    ).distinct(Result.normalized_url)

    include_filters = [f.url for f in study.study_url_filters if f.include and f.url]
    if include_filters:
        open_organic_query = open_organic_query.filter(or_(*[Result.normalized_url.contains(clean_filter_string(f)) for f in include_filters]))

    exclude_filters = [f.url for f in study.study_url_filters if f.exclude and f.url]
    if exclude_filters:
        open_organic_query = open_organic_query.filter(and_(*[~Result.normalized_url.contains(clean_filter_string(f)) for f in exclude_filters]))

    all_valid_organic_tasks = open_organic_query.all()
    
    total_organic_tasks = 0
    if study.limit_per_participant and study.max_results_per_participant is not None:
        total_organic_tasks = min(len(all_valid_organic_tasks), study.max_results_per_participant)
    else:
        total_organic_tasks = len(all_valid_organic_tasks)

    total_ai_tasks = base_query.filter(Answer.status == 0, Answer.result_ai_id.isnot(None)).count()
    total_chatbot_tasks = base_query.filter(Answer.status == 0, Answer.result_chatbot_id.isnot(None)).count()
    
    total_open_tasks = total_organic_tasks + total_ai_tasks + total_chatbot_tasks
    answers_closed_raw = base_query.filter(Answer.status.in_([1, 2])).count()
    answers_all_raw = answers_closed_raw + total_open_tasks

    # FIX: Divide by question count to get item count
    questions_count = len(study.questions) or 1
    answers_all = answers_all_raw // questions_count
    answers_closed = answers_closed_raw // questions_count
    
    percentage = (answers_closed / answers_all * 100) if answers_all > 0 else 0
    
    return render_template('assessments/assessments.html', 
                           participant=participant, study=study, answers_all=answers_all, 
                           answers_closed=answers_closed, pct=round(percentage))


@app.route('/assessment/<participant_id>/<study_id>', methods=["GET", "POST"])
def assessment(participant_id, study_id):
    logout_user()
    participant = Participant.query.get_or_404(participant_id)
    study = Study.query.get_or_404(study_id)
    db.session.expire_all()

    open_result_tasks_query = db.session.query(Answer.result_id).filter(
        Answer.participant_id == participant.id,
        Answer.study_id == study.id,
        Answer.status == 0,
        Answer.result_id.isnot(None)
    ).join(Result).join(Result.source_associations).filter(
        ResultSource.progress == 1, # Hier wird geprüft, ob die Quelle bereit ist
        Result.normalized_url.isnot(None),
        Result.normalized_url != ""
    ).distinct()

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
    
    next_answer = db.session.query(Answer).filter(
        Answer.participant_id == participant.id,
        Answer.study_id == study.id,
        Answer.status == 0,
        or_(
            Answer.result_id.in_(valid_result_ids),
            Answer.result_ai_id.in_(valid_ai_ids),
            Answer.result_chatbot_id.in_(valid_chatbot_ids)
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
            # Automatisch überspringen, wenn keine Vorschau vorhanden ist
            if not (task_item.sources and task_item.sources[0] and task_item.sources[0].bin):
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