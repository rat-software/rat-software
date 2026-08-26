"""
Participant module for the RAT application.

This module handles participant workflow loops, including generation metrics 
for researcher dashboards, individual task completion stats for participant 
landing panels, concurrent signup pipelines, and session recovery routes.
"""

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
    """
    Renders the study participant tracking overview panel for the researcher dashboard.

    Calculates task progression markers (answered, skipped, and open counts)
    for every connected user relative to fixed structural study limit parameters.

    Args:
        id (str): Unique primary identifier of the parent Study record.

    Returns:
        str: Rendered researcher-facing participants list view layout.
    """
    study = Study.query.get_or_404(id)
    info = []
    questions_count = len(study.questions) or 1

    for participant in study.participants:
        if study.group_by_query:
            all_ans = db.session.query(Answer).filter(
                Answer.participant_id == participant.id,
                Answer.study_id == study.id
            ).all()
            
            seen_queries = set()
            open_queries = set()
            
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
                    if ans.status == 0: open_queries.add(q_id)
                    
            closed_count = len(seen_queries) - len(open_queries)
            skipped_count = 0 
            
            if study.limit_by_query and study.max_queries_per_participant and study.max_queries_per_participant > 0:
                all_count = study.max_queries_per_participant
                if closed_count > all_count: closed_count = all_count
            else:
                all_count = len(seen_queries) + (1 if len(open_queries) == 0 else 0)
                
            open_count = all_count - closed_count
            if open_count < 0: open_count = 0
            
        else:
            base_query = db.session.query(Answer).filter(
                Answer.participant_id == participant.id,
                Answer.study_id == study.id
            )
            
            closed_count = base_query.filter(Answer.status == 1).count() // questions_count
            skipped_count = base_query.filter(Answer.status == 2).count() // questions_count
            finished_count = closed_count + skipped_count
            open_ans_count = base_query.filter(Answer.status == 0).count() // questions_count

            if study.limit_per_participant and (study.max_results_per_participant or 0) > 0:
                all_count = study.max_results_per_participant
                if finished_count > all_count: all_count = finished_count
            else:
                all_count = finished_count + open_ans_count
                if open_ans_count == 0:
                    all_count = finished_count + 1

            open_count = all_count - finished_count
            if open_count < 0: open_count = 0

        info.append([participant, all_count, open_count, closed_count, skipped_count])

    return render_template('participants/participants.html', study=study, info=info)


@app.route('/participant/<id>', methods=["GET", "POST"])
def participant(id):
    """
    Renders the task gateway cockpit or resume panel for an active participant.

    Compiles task stats across all studies linked to the user profile 
    and handles file compilation downloads for localized session identity backups.

    Args:
        id (str): Unique primary identifier matching the target Participant record.

    Returns:
        Response: Rendered participant landing page context or secure identity text stream.
    """
    logout_user()
    participant = Participant.query.get_or_404(id)
    base = request.url_root
    form = ConfirmationForm()
    
    info = []
    
    for study in participant.studies:
        questions_count = len(study.questions)
        if questions_count == 0:
            info.append([study.id, 0, 0, 0, 0])
            continue

        # WICHTIG: Prüft BEIDE Schalter
        if study.group_by_query and study.limit_by_query:
            # DASHBOARD ZÄHLT QUERIES (Damit es nicht zu früh "Done" anzeigt)
            all_ans = db.session.query(Answer).filter(Answer.participant_id == participant.id, Answer.study_id == study.id).all()
            seen_queries = set()
            open_queries = set()
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
                    if ans.status == 0: open_queries.add(q_id)
            
            closed_count = len(seen_queries) - len(open_queries)
            skipped_count = 0 
            
            if (study.max_queries_per_participant or 0) > 0:
                all_count = study.max_queries_per_participant
            else:
                all_count = len(seen_queries) + (1 if len(open_queries) == 0 else 0)
                
            open_count = all_count - closed_count
            if open_count < 0: open_count = 0
            
            info.append([study.id, all_count, open_count, closed_count, skipped_count])
            
        else:
            # DASHBOARD ZÄHLT ITEMS
            base_query = db.session.query(Answer).filter(Answer.participant_id == participant.id, Answer.study_id == study.id)
            
            closed_count = (base_query.filter(Answer.status == 1).count() // questions_count)
            skipped_count = (base_query.filter(Answer.status == 2).count() // questions_count)
            finished_count = closed_count + skipped_count
            open_ans_count = (base_query.filter(Answer.status == 0).count() // questions_count)

            if study.limit_per_participant and (study.max_results_per_participant or 0) > 0:
                all_count = study.max_results_per_participant
                if finished_count > all_count: all_count = finished_count
            else:
                all_count = finished_count + open_ans_count
                if open_ans_count == 0:
                    all_count = finished_count + 1 

            open_count = all_count - finished_count
            if open_count < 0: open_count = 0

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
    """
    Registers a new anonymous participant and assigns them to the chosen study context.

    Generates safe serialized account handles using auto-increment routines without 
    requiring restrictive thread locking mechanisms.

    Args:
        study_id (str): Unique primary identifier of the chosen targeted Study.

    Returns:
        Response: A redirect instruction to the personal cockpit screen, or the access view.
    """
    logout_user()
    form = JoinForm()
    if not form.is_submitted() or not form.new.data:
        if form.is_submitted() and form.returning.data:
            return redirect(url_for('returning_participant', study_id=study_id))
        return render_template('participants/join.html', form=form)

    # No pessimistic locking required
    study = Study.query.get_or_404(study_id)
    
    # Generate new unique participant parameters
    max_id = db.session.query(func.max(Participant.id)).scalar() or 0
    participant = Participant(
        name='user' + str(max_id + 1),
        created_at=datetime.now(),
        password=random.randint(1000, 9999)
    )
    participant.studies.append(study)
    db.session.add(participant)

    # Directly commit data transactions without temporary placeholders
    db.session.commit()
    
    return redirect(url_for('participant', id=participant.id))

@app.route('/study/<study_id>/participant/returning', methods=["GET", "POST"])
@app.route('/returning/<study_id>', methods=["GET", "POST"])
def returning_participant(study_id):
    """
    Authenticates a returning user via explicit credentials to restore past tracking sessions.

    Args:
        study_id (str): Unique primary identifier of the targeted active Study.

    Returns:
        Response: Forwarding routing rules to ongoing assessment loops or retry panels.
    """
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

    return render_template('participants/returning.html', form=form)


@app.route('/participant/<id>/<code>/resume')
@app.route('/resume/<id>/<code>')
def resume(id, code):
    """
    Restores sessions using secure authenticated quick-access signature link parameters.

    Args:
        id (str): Unique primary key identifier of the restoring Participant.
        code (str): Plain-text access code key mapped to user password records.

    Returns:
        Response: Redirect routing leading safely back onto matching cockpit setups.
    """
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
    """
    Deletes a participant profile along with all associated manual answer records.

    Args:
        id (str): Unique primary key identifier of the target Participant record.

    Returns:
        Response: Redirect routing rules returning back onto central tracking dashboards.
    """
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