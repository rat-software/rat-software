from .. import app, db
from ..forms import AnswerForm
from ..helpers import get_options
from app.models import Study, Participant, Answer, Question, Result
from flask import render_template, flash, redirect, url_for
from sqlalchemy import asc
from datetime import datetime
from sqlalchemy.sql.expression import func


@app.route('/<study_id>/participant/<participant_id>/assessments')
def assessments(participant_id, study_id):
    participant = Participant.query.get(participant_id)
    study = Study.query.get(study_id)

    answers = Answer.query.filter(Answer.participant == participant, Answer.study == study)
    answers_all = answers.count()
    print(answers_all)
    answers_open = answers.filter(Answer.status == 0).count()
    answers_closed = answers.filter(Answer.status != 0).count()

    if answers_closed != 0:
        pct = round(answers_closed / answers_all * 100)
    else:
        pct = 0

    return render_template('assessments/assessments.html',
                           participant=participant,
                           study=study,
                           answers_all=answers_all,
                           answers_open=answers_open,
                           answers_closed=answers_closed,
                           pct=pct)


@app.route('/assessment/<participant_id>/<study_id>', methods=["GET", "POST"])
def assessment(participant_id, study_id):
    participant = Participant.query.get(participant_id)
    study = Study.query.get(study_id)

    def check_source(answer):
        if answer.result.source:
            return True
        else:
            return False

    def get_answer():
        answer = db.session.query(Answer).\
                            filter(Answer.participant == participant,
                                   Answer.study == study,
                                   Answer.status == 0).\
                            first()

        if check_source(answer):
            return answer
        else:
            print(answer.result.source)
            get_answer()

    answer = get_answer()

    form = get_options(answer.question)

    answers = Answer.query.filter(Answer.participant == participant, Answer.study == study)
    all = answers.count()
    closed = answers.filter(Answer.status != 0).count()

    if closed != 0:
        pct = round(closed / all * 100)
    else:
        pct = 0

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
                           all=all,
                           closed=closed,
                           pct=pct)
