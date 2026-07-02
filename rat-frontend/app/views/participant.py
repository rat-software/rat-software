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
    # --- Repariert für das Dashboard des Admins/Forschers ---
    study = Study.query.get_or_404(id)
    info = []
    questions_count = len(study.questions) or 1

    for participant in study.participants:
        query = db.session.query(Answer).filter(
            Answer.participant == participant,
            Answer.study == study
        )
        
        closed_count = query.filter(Answer.status == 1).count() // questions_count
        skipped_count = query.filter(Answer.status == 2).count() // questions_count
        finished_count = closed_count + skipped_count

        # JIT Target Calculation
        if study.limit_by_query and (study.max_queries_per_participant or 0) > 0:
            all_count = study.max_queries_per_participant
        elif study.limit_per_participant and (study.max_results_per_participant or 0) > 0:
            all_count = study.max_results_per_participant
        else:
            all_count = finished_count + 1

        open_count = all_count - finished_count
        if open_count < 0: open_count = 0

        info.append([participant, all_count, open_count, closed_count, skipped_count])

    return render_template('participants/participants.html', study=study, info=info)


@app.route('/participant/<id>', methods=["GET", "POST"])
def participant(id):
    # --- Repariert für das Dashboard des Probanden (Der START-Button) ---
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

        base_query = db.session.query(Answer).filter(
            Answer.participant_id == participant.id,
            Answer.study_id == study.id
        )
        
        closed_count = (base_query.filter(Answer.status == 1).count() // questions_count)
        skipped_count = (base_query.filter(Answer.status == 2).count() // questions_count)
        finished_count = closed_count + skipped_count

        # JIT Target Calculation - Fragt die globalen Studien-Limits ab
        if study.limit_by_query and (study.max_queries_per_participant or 0) > 0:
            all_count = study.max_queries_per_participant
        elif study.limit_per_participant and (study.max_results_per_participant or 0) > 0:
            all_count = study.max_results_per_participant
        else:
            # Endlos-Studie: Immer +1, damit der Start-Button als "Offen" angezeigt wird!
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
    logout_user()
    form = JoinForm()
    if not form.is_submitted() or not form.new.data:
        if form.is_submitted() and form.returning.data:
            return redirect(url_for('returning_participant', study_id=study_id))
        return render_template('participants/join.html', form=form)

    # 1. KEINE PESSIMISTISCHE SPERRE MEHR!
    study = Study.query.get_or_404(study_id)
    
    # 2. Neuen Teilnehmer generieren
    max_id = db.session.query(func.max(Participant.id)).scalar() or 0
    participant = Participant(
        name='user' + str(max_id + 1),
        created_at=datetime.now(),
        password=random.randint(1000, 9999)
    )
    participant.studies.append(study)
    db.session.add(participant)

    # 3. Direkt speichern und weiterleiten. Keine Dummys mehr!
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

    return render_template('participants/returning.html', form=form)


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