from .. import app, db
from ..forms import QuestionForm, ConfirmationForm, ImportQuestionsForm
from ..models import Study, Option, QuestionType, Question
from ..helpers import get_options
from flask import Blueprint, render_template, flash, redirect, url_for, request, Response
from flask_security import login_required
import json
from datetime import datetime

@app.route("/study/<id>/questions", methods=['GET', 'POST'])
@login_required
def questions(id):
    """
    Displays a paginated list of questions for a specific study.
    """
    study = Study.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Question).filter(Question.study_id == study.id).order_by(Question.position).paginate(page=page, per_page=10)

    return render_template("questions/questions.html",
                           study=study,
                           pagination=pagination)


@app.route("/question/<id>", methods=["GET", "POST"])
@login_required
def question(id):
    """
    Displays details of a specific question, including its options.
    """
    question = Question.query.get_or_404(id)
    form = get_options(question)

    return render_template("questions/question.html",
                           question=question,
                           form=form)


@app.route("/study/<id>/question/new", methods=["GET", "POST"])
@login_required
def new_question(id):
    """
    Handles the creation of a new question for a specific study. 
    """
    study = Study.query.get(id)
    q_count = db.session.query(Question).filter(Question.study == study).count()
    q_pos = q_count + 1
    form = QuestionForm()
    form.q_type.choices = [(q.display, q.name) for q in QuestionType.query.all()]

    if form.is_submitted():
        # Initialize position counter for options
        i = 1
        options = []

        # Process options based on the selected question type
        if form.q_type.data == "scale_number":
            for k, v in form.ranges.data[0].items():
                if k != "csrf_token":
                    o = Option()
                    o.value = str(v)
                    o.label = str(k)
                    o.position = i
                    options.append(o)
                    i += 1

        if form.q_type.data in ["true_false", "likert_scale", "multiple_choice"]:
            for data in form.options.data:
                o = Option()
                o.value = data["value"]
                o.label = data["label"]
                o.position = i
                options.append(o)
                i += 1

        # Get the question type from the database
        type = QuestionType.query.filter_by(display=form.q_type.data).first()

        # Create a new question and associate it with the study and options
        q = Question()
        q.title = form.text.data
        q.questiontype = type
        q.position = form.position.data
        q.study = Study.query.get(id)
        q.options.extend(options)

        # Add the new question and options to the database
        insert = options
        insert.append(q)
        db.session.add_all(insert)
        db.session.commit()

        flash("Your question has been created.", "success")
        return redirect(url_for("questions", id=id))

    return render_template("questions/new_question.html", form=form, q_pos=q_pos)


@app.route("/question/<id>/delete", methods=["GET", "POST"])
@login_required
def delete_question(id):
    """
    Handles the deletion of a specific question and its associated options and answers.
    """
    question = Question.query.get_or_404(id)
    form = ConfirmationForm()

    if form.is_submitted():
        if form.submit.data:
            study_id = question.study.id

            # Delete associated answers and options
            for answer in question.answers:
                db.session.delete(answer)
            for option in question.options:
                db.session.delete(option)
            db.session.delete(question)

            db.session.commit()

            flash('Question deleted', 'success')
            return redirect(url_for('questions', id=study_id))

    return render_template('questions/delete_question.html',
                           form=form,
                           question=question)

@app.route("/study/<id>/questions/export")
@login_required
def export_questions_json(id):
    """
    Exports all questions and options for a study as a JSON file.
    """
    study = Study.query.get_or_404(id)
    questions = Question.query.filter_by(study_id=study.id).order_by(Question.position).all()
    
    export_data = []
    
    for q in questions:
        q_data = {
            'title': q.title,
            'type_display': q.questiontype.display, 
            'position': q.position,
            'options': [],
            'ranges': [] 
        }
        
        # Serialize Options
        for opt in q.options:
            q_data['options'].append({
                'label': opt.label,
                'value': opt.value,
                'position': opt.position
            })
            
        export_data.append(q_data)
    
    # Create JSON string
    json_str = json.dumps(export_data, indent=4)
    
    # Create response as file download
    filename = f"questions_export_study_{study.id}_{datetime.now().strftime('%Y%m%d')}.json"
    
    return Response(
        json_str,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )


@app.route("/study/<id>/questions/import", methods=["GET", "POST"])
@login_required
def import_questions_json(id):
    """
    Imports questions from a JSON file. Checks for duplicates based on title.
    """
    study = Study.query.get_or_404(id)
    form = ImportQuestionsForm()
    
    if form.validate_on_submit():
        f = form.file.data
        try:
            data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON must be a list of questions")
            
            imported_count = 0
            skipped_count = 0
            
            # Get current question count to append new ones at the end
            current_count = db.session.query(Question).filter(Question.study_id == study.id).count()
            position_offset = current_count + 1
            
            for index, item in enumerate(data):
                title = item.get('title')
                type_display = item.get('type_display')
                
                # 1. Find Question Type
                q_type = QuestionType.query.filter_by(display=type_display).first()
                if not q_type:
                    flash(f"Unknown question type '{type_display}' for question '{title}'. Skipped.", "warning")
                    skipped_count += 1
                    continue
                
                # 2. Check for Duplicates in THIS study
                exists = Question.query.filter_by(
                    study_id=study.id, 
                    title=title, 
                    questiontype_id=q_type.id
                ).first()
                
                if exists:
                    skipped_count += 1
                    continue
                
                # 3. Create Question
                new_q = Question()
                new_q.title = title
                new_q.questiontype = q_type
                new_q.study_id = study.id
                new_q.position = position_offset + index 
                
                # 4. Create Options
                new_options = []
                if 'options' in item:
                    for opt_data in item['options']:
                        o = Option()
                        o.label = opt_data.get('label')
                        o.value = opt_data.get('value')
                        o.position = opt_data.get('position')
                        new_options.append(o)
                
                new_q.options.extend(new_options)
                
                # Add to session
                db.session.add(new_q)
                for o in new_options:
                    db.session.add(o)
                
                imported_count += 1
            
            db.session.commit()
            
            if imported_count > 0:
                flash(f"Successfully imported {imported_count} questions.", "success")
            if skipped_count > 0:
                flash(f"Skipped {skipped_count} duplicates or invalid entries.", "warning")
                
            return redirect(url_for('questions', id=study.id))
            
        except Exception as e:
            flash(f"Error importing file: {str(e)}", "danger")
            
    return render_template("questions/import_questions.html", study=study, form=form)