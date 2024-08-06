from .. import app, db
from ..forms import AnswerForm
from ..helpers import get_options
from app.models import Study, Participant, Answer, Question, Result, Source
from flask import render_template, flash, redirect, url_for
from sqlalchemy import asc
from flask_login import logout_user
from datetime import datetime
from sqlalchemy.sql.expression import func
from sqlalchemy import text

@app.route('/<study_id>/participant/<participant_id>/assessments')
def assessments(participant_id, study_id):
    """
    Renders a summary of assessments for a specific participant in a study.

    Args:
        participant_id (str): The ID of the participant.
        study_id (str): The ID of the study.

    Returns:
        Rendered HTML template for the assessments summary page.
    """
    # Log out the user before showing assessments
    logout_user()
    
    # Retrieve the participant and study from the database
    participant = Participant.query.get(participant_id)
    study = Study.query.get(study_id)

    # Set up query to filter answers based on participant and study
    query = db.session.query(Answer).filter(Answer.source_status_code == 200,
                                            Answer.participant == participant,
                                            Answer.study == study)
    
    # Get counts of different types of answers
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
    """
    Handles the assessment process for a participant in a study.

    Args:
        participant_id (str): The ID of the participant.
        study_id (str): The ID of the study.

    Returns:
        Rendered HTML template for the assessment page or redirects based on form submission.
    """
    # Log out the user before showing the assessment
    logout_user()
    
    # Retrieve the participant and study from the database
    participant = Participant.query.get(participant_id)
    study = Study.query.get(study_id)

    # Set up query to filter open assessments based on participant and study
    query = db.session.query(Answer).filter(Answer.source_status_code == 200,
                                            Answer.participant == participant,
                                            Answer.study == study)
    
    

    try:
        
        # Retrieve counts of answers using raw SQL for better performance
        counter = db.session.execute(text("select count(answer.id) from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant"), {'id_study': str(study_id), 'id_participant': str(participant_id)})
        for c in counter:
            all_answers = c[0]

        counter = db.session.execute(text("select count(answer.id) from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant and answer.status = 0"), {'id_study': str(study_id), 'id_participant': str(participant_id)})
        for c in counter:
            open_answers = c[0]

        counter = db.session.execute(text("select count(answer.id) from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant and answer.status = 1"), {'id_study': str(study_id), 'id_participant': str(participant_id)})
        for c in counter:
            closed_answers = c[0]

        counter = db.session.execute(text("select count(answer.id) from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant and answer.status = 2"), {'id_study': str(study_id), 'id_participant': str(participant_id)})
        for c in counter:
            skipped_answers = c[0]

        # Calculate the percentage of completed assessments
        if closed_answers != 0:
            pct = (closed_answers + skipped_answers) / all_answers * 100
        else:
            pct = 0

        # Retrieve the next available assessment
        #sql = text("select answer.id from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant and answer.status = 0 order by result.query ASC LIMIT 1") 
        answers = db.session.execute(text("select answer.id from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant and answer.status = 0 order by result.query ASC LIMIT 1"), {'id_study': str(study_id), 'id_participant': str(participant_id)})
        for a in answers:
            id_answer = a[0]        

        # Get the specific answer object
        answer = db.session.query(Answer).filter(Answer.id == id_answer).first()

    except Exception as e:
        print(e)
        # In case of error, set answer to False
        answer = False

    if answer:
        # Get the form options for the answer's question
        form = get_options(answer.question)

    else:
        # Notify user if no more assessments are available and redirect
        flash('No more available assessments.', 'info')
        return redirect(url_for("participant", id=participant.id))

    if form.is_submitted():
        if form.skip.data:
            # Mark assessment as skipped
            answer.status = 2
            answer.created_at = datetime.now()
            db.session.commit()
            flash('The assessment has been skipped.', 'info')
        else:
            # Save the assessment answer
            answer.value = form.data[answer.question.questiontype.display]
            answer.status = 1
            answer.created_at = datetime.now()
            db.session.commit()
            flash('Your assessment has been saved.', 'success')

        # Redirect to the next assessment
        return redirect(url_for("assessment",
                                participant_id=participant.id,
                                study_id=study.id))

    return render_template('assessments/assessment.html',
                           form=form,
                           answer=answer,
                           all=all_answers,
                           closed=closed_answers,
                           pct=pct)
