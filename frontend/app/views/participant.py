from .. import app, db
from app.models import Study, Participant, Answer, Result, Question
from ..forms import JoinForm, ParticipantLogInForm
from flask import Blueprint, render_template, flash, redirect, url_for, request, send_file
from datetime import datetime
from flask_login import logout_user
import random
from io import BytesIO
from sqlalchemy import func, update
import sqlalchemy
#bp = Blueprint('participant', __name__)

@app.route('/study/<id>/participants')
def participants(id):
    study = Study.query.get(id)
    info = []
    for participant in study.participants:
        query = db.session.query(Answer).filter(Answer.source_status_code == 200,
                                                Answer.participant == participant,
                                                Answer.study == study)
        all = query.count()
        open = query.filter(Answer.status == 0).count()
        closed = query.filter(Answer.status == 1).count()
        skipped = query.filter(Answer.status == 2).count()


        info.append([participant, all, open, closed, skipped])

    return render_template('participants/participants.html',
                           study=study,info=info)


@app.route('/participant/<id>', methods=["GET", "POST"])
def participant(id):
    logout_user()
    participant = Participant.query.get(id)
    base = request.url_root

    # update source status code based on source table
    db.session.execute(sqlalchemy.sql.text("update answer set source_status_code = source.status_code from source left join result_source on source.id = result_source.source where answer.result = result_source.result"))
    db.session.commit()

    #create list to display studies and open assessments
    info = []
    for study in participant.studies:
        query = db.session.query(Answer).filter(Answer.source_status_code == 200,
                                                Answer.participant == participant,
                                                Answer.study == study)
        all = query.count()
        open = query.filter(Answer.status == 0).count()
        closed = query.filter(Answer.status == 1).count()
        skipped = query.filter(Answer.status == 2).count()


        info.append([study.id, all, open, closed, skipped])

    # create txt file for resume link
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
                           base=base)


@app.route('/study/<study_id>/participant/new', methods=["GET", "POST"])
@app.route('/join/<study_id>', methods=["GET", "POST"])
def new_participant(study_id):
    logout_user()
    form = JoinForm()
    if form.is_submitted():
        # CREATE NEW PARTICIPANT
        if form.new.data:
            study = Study.query.get(study_id)
            count = Participant.query.count()


            max_ids = db.session.query(func.max(Participant.id)).scalar()
            max_id = db.session.query(Participant).filter(Participant.id == max_ids).first()
            if max_id:
                u_name = max_id.id + 1
            else:
                u_name = 1

            participant = Participant()
            participant.name = 'user' + str(u_name)
            participant.created_at = datetime.now()
            participant.studies.append(study)
            participant.password = random.randint(1000, 9999)

            db.session.add(participant)
            db.session.commit()

            ## make quicker with union or join sql?
            for result in db.session.query(Result).filter(Result.study == study).all():
                for question in db.session.query(Question).filter(Question.study == study).all():
                    answer = Answer()
                    answer.study = study
                    answer.result = result
                    answer.question = question
                    answer.participant = participant
                    answer.status = 0
                    answer.created_at = datetime.now()

                    db.session.add(answer)
                db.session.commit()

            return redirect(url_for('participant', id=participant.id))

        # REDIRECT TO LOG IN FOR RETURNING PARTICIPANTS
        if form.returning.data:
            return redirect(url_for('returning_participant', study_id=study_id))

    return render_template('participants/join.html',
                           form=form)


@app.route('/study/<study_id>/participant/returning', methods=["GET", "POST"])
@app.route('/returning/<study_id>', methods=["GET", "POST"])
def returning_participant(study_id):
    logout_user()
    form = ParticipantLogInForm()

    if form.is_submitted():
        check_user = db.session.query(
            Participant.query.filter(
                Participant.name == form.username.data).exists()).scalar()

        if check_user:
            participant = Participant.query.filter(
                Participant.name == form.username.data).first()

            if int(participant.password) == int(form.password.data):
                study = Study.query.get(study_id)
                if study not in participant.studies:
                    participant.studies.append(study)
                    db.session.commit()

                flash('Welcome back, '+ participant.name, 'success')
                return redirect(url_for('assessment', participant_id=participant.id, study_id=study.id))
            else:
                flash('Code is incorrect', 'danger')
        else:
            flash('Username does not exsist.', 'danger')

    return render_template('participants/returning.html',
                           form=form)


@app.route('/participant/<id>/<code>/resume')
@app.route('/resume/<id>/<code>')
def resume(id, code):
    logout_user()
    participant = Participant.query.get(id)
    if int(participant.password) == int(code):
        flash('Welcome back!', 'success')
        return redirect(url_for('participant', id=id))
    else:
        flash('Code invalid.', 'danger')
        return redirect(url_for('home'))


@app.route('/participant/<id>/delete', methods=["GET", "POST"])
def delete_participant(id):
    logout_user()
    participant = Participant.query.get(id)

    db.session.delete(participant)

    # commit to db
    db.session.commit()

    flash('Participant deleted', 'success')
    return redirect(url_for('dashboard'))
