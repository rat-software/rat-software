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
    #print(query)
    # get number of assessments

    #hotfix
  
    try:
        sql = text("select count(answer.id) from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant")
        counter = db.engine.execute(sql, id_study = str(study_id), id_participant = str(participant_id))

        for c in counter:
            all_answers = (c[0])

        #all_answers = query.count()        
        
        # sql = text("select count(*) from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant order by query ASC") 
        # all_answers = db.engine.execute(sql, id_study = str(study_id), id_participant = str(participant_id))

        #open_answers = query.filter(Answer.status == 0).count()

        sql = text("select count(answer.id) from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant and answer.status = 0")
        counter = db.engine.execute(sql, id_study = str(study_id), id_participant = str(participant_id))

        for c in counter:
            open_answers = (c[0])    
        
        #closed_answers = query.filter(Answer.status == 1).count()

        sql = text("select count(answer.id) from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant and answer.status = 1")
        counter = db.engine.execute(sql, id_study = str(study_id), id_participant = str(participant_id))

        for c in counter:
            closed_answers = (c[0])    
        
        #skipped_answers = query.filter(Answer.status == 2).count()

        sql = text("select count(answer.id) from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant and answer.status = 2")
        counter = db.engine.execute(sql, id_study = str(study_id), id_participant = str(participant_id))

        for c in counter:
            skipped_answers = (c[0])    

        print(all_answers, open_answers, closed_answers, skipped_answers)

        if closed_answers != 0:
            pct = (closed_answers + skipped_answers) / all_answers * 100
        else:
            pct = 0

        sql = text("select answer.id from answer, result where result.id = answer.result AND answer.study = :id_study and source_status_code = 200 and participant = :id_participant and answer.status = 0 order by result.query ASC LIMIT 1") 
        answers = db.engine.execute(sql, id_study = str(study_id), id_participant = str(participant_id))

        for a in answers:
            id_answer =a[0]        

        #print(id_answer)
    

        # get first available assessment
        #answer = query.filter(Answer.status == 0).first()

        

        answer = db.session.query(Answer).filter(Answer.id==id_answer).first()

    except:
        answer = False
    

    if answer:
        # get answer options
        form = get_options(answer.question)
        print(answer.id)
        print(answer.question)

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

            
            print(answer)
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
