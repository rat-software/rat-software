from .. import app, db
from ..forms import AnswerForm
from ..helpers import get_options
from app.models import Study, Participant, Answer, Question, Result, Source
from flask import render_template, flash, redirect, url_for
from sqlalchemy import asc
from flask_login import logout_user
from datetime import datetime
from sqlalchemy.sql.expression import func


@app.route('/<study_id>/participant/<participant_id>/assessments')
def assessments(participant_id, study_id):
    logout_user()
    participant = Participant.query.get(participant_id)
    study = Study.query.get(study_id)

    # set up baseline query
    query = db.session.query(Answer).filter(Answer.source_status_code == 200,
                                            Answer.participant == participant,
                                            Answer.study == study)

    # get number of assessments
    all_answers = query.count()
    open_answers = query.filter(Answer.status == 0).count()
    closed_answers = query.filter(Answer.status == 1).count()
    skipped_answers = query.filter(Answer.status == 2).count()


    return render_template('assessments/assessments.html',
                           participant=participant,
                           study=study,
                           all_answers=all_answers,
                           open_answers=open_answers,
                           closed_answers=closed_answers,
                           skipped_answers=skipped_answers)


@app.route('/assessment/<participant_id>/<study_id>', methods=["GET", "POST"])
def assessment(participant_id, study_id):
    logout_user()
    participant = Participant.query.get(participant_id)
    study = Study.query.get(study_id)

    # get assessment for participant from study that is open, has source
    # if no answer: return to overview page

    # if answer:
    # get answer choices
    # calculate status of

    # query for all open assessments
    query = db.session.query(Answer).filter(Answer.source_status_code == 200,
                                            Answer.participant == participant,
                                            Answer.study == study)
    print(query)
    # get number of assessments
    all_answers = query.count()
    open_answers = query.filter(Answer.status == 0).count()
    closed_answers = query.filter(Answer.status == 1).count()
    skipped_answers = query.filter(Answer.status == 2).count()

    print(all_answers, open_answers, closed_answers, skipped_answers)

    if closed_answers != 0:
        pct = closed_answers / all_answers * 100
    else:
        pct = 0

    # get first available assessment
    answer = query.filter(Answer.status == 0).first()
    if answer:
        # get answer options
        form = get_options(answer.question)
        print(answer.id)

    else:
        flash('No more available assessments.', 'info')
        return redirect(url_for("participant", id=participant.id))


    if form.is_submitted():
        if form.skip.data:
            answer.status = 2
            answer.created_at = datetime.now()

            db.session.commit()
            flash('The assessment has been skipped.', 'info')
        else:
            answer.value = form.data[answer.question.questiontype.display]
            answer.status = 1
            answer.created_at = datetime.now()

            db.session.commit()
            flash('Your assessment has been saved.', 'success')

        return redirect(url_for("assessment",
                                participant_id=participant.id,
                                study_id=study.id))

    return render_template('assessments/assessment.html',
                           form=form,
                           answer=answer,
                           all=all_answers,
                           closed=closed_answers,
                           pct=pct)
