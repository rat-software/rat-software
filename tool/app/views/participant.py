from .. import app, db
from app.models import Study, Participant, Answer, Result, Question
from ..forms import JoinForm, ParticipantLogInForm
from flask import render_template, flash, redirect, url_for, request, send_file
from datetime import datetime
import random
from io import BytesIO


@app.route('/study/<id>/participants')
def participants(id):
    study = Study.query.get(id)

    return render_template('participants/participants.html',
                           study=study)


@app.route('/participant/<id>', methods=["GET", "POST"])
def participant(id):
    participant = Participant.query.get(id)
    base = request.url_root

    #create list to display studies and open assessments
    info = []
    for study in participant.studies:
        answers_all = Answer.query.filter(Answer.participant == participant,
                                             Answer.study == study).count()
        answers_closed = Answer.query.filter(Answer.participant == participant,
                                           Answer.study == study,
                                           Answer.status != 0).count()

        info.append([study.id, study.name, answers_closed, answers_all])

    # create txt file for resume link
        if request.method == 'POST':
            if 'download' in request.form:
                buffer = BytesIO()
                return_url = base + "resume/" + str(participant.id) + '-' + str(participant.password)
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
    form = JoinForm()
    if form.is_submitted():
        # CREATE NEW PARTICIPANT
        if form.new.data:
            study = Study.query.get(study_id)
            count = Participant.query.count()

            participant = Participant()
            participant.name = 'user' + str(count+1)
            participant.created_at = datetime.now()
            participant.studies.append(study)
            participant.password = random.randint(1000, 9999)

            db.session.add(participant)
            db.session.commit()

            ## make quicker with union or join sql?
            for result in db.session.query(Result).filter(Result.study == study).limit(50):
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
                return redirect(url_for('assessments', participant_id=participant.id))
            else:
                flash('Code is incorrect', 'danger')
        else:
            flash('Username does not exsist.', 'danger')

    return render_template('participants/returning.html',
                           form=form)


@app.route('/participant/<id>/<code>/resume')
@app.route('/resume/<id>-<code>')
def resume(id, code):
    participant = Participant.query.get(id)
    if participant.password == code:
        flash('Welcome back!', 'success')
        return redirect(url_for('participant', id=id))
    else:
        flash('Code invalid.', 'danger')
        return redirect(url_for('home'))

@app.route('/participant/<id>/delete', methods=["GET", "POST"])
def delete_participant(id):
    participant = Participant.query.get(id)
    db.session.delete(participant)

    # commit to db
    db.session.commit()

    flash('Study deleted', 'success')
    return redirect(url_for('dashboard'))
