from .. import app, db
from ..forms import QuestionForm, AnswerForm, ConfirmationForm
from ..models import Study, Option, QuestionType, Question
from ..helpers import get_options
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_security import login_required, current_user
#bp = Blueprint('question', __name__)

@app.route("/study/<id>/questions", methods=['GET', 'POST'])
@login_required
def questions(id):
    """
    Displays a paginated list of questions for a specific study.

    Args:
        id (int): The ID of the study whose questions are to be displayed.

    Returns:
        Renders the questions page with the study and paginated questions.
    """
    study = Study.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Question).filter(Question.study_id == study.id).paginate(page=page, per_page=10)

    

    return render_template("questions/questions.html",
                           study=study,
                           pagination=pagination)


@app.route("/question/<id>", methods=["GET", "POST"])
@login_required
def question(id):
    """
    Displays details of a specific question, including its options.

    Args:
        id (int): The ID of the question to be displayed.

    Returns:
        Renders the question details page with the question and its options.
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

    Args:
        id (int): The ID of the study to which the new question will be added.

    Returns:
        Renders the new question form page or redirects to the study page if the question is created.
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
        return redirect(url_for("study", id=id))

    return render_template("questions/new_question.html", form=form, q_pos=q_pos)


@app.route("/question/<id>/delete", methods=["GET", "POST"])
def delete_question(id):
    """
    Handles the deletion of a specific question and its associated options and answers.

    Args:
        id (int): The ID of the question to be deleted.

    Returns:
        Renders the delete confirmation page or redirects to the study page if the question is deleted.
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
            return redirect(url_for('study', id=study_id))

    return render_template('questions/delete_question.html',
                           form=form,
                           question=question)

    # Note: The commented section below is not executed as part of this code
    # delete question
    # delete all related options and answers
