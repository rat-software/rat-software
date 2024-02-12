from .. import app, db
from ..forms import QuestionForm, AnswerForm, ConfirmationForm
from ..models import Study, Option, QuestionType, Question
from ..helpers import get_options
from flask import render_template, flash, redirect, url_for, request
from flask_security import login_required, current_user


@app.route("/study/<id>/questions", methods=['GET', 'POST'])
@login_required
def questions(id):
    study = Study.query.get_or_404(id)

    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Question).filter(Question.study_id == study.id).paginate(page, per_page=10)

    return render_template("questions/questions.html",
                           study=study,
                           pagination=pagination)


@app.route("/question/<id>", methods=["GET", "POST"])
@login_required
def question(id):
    question = Question.query.get_or_404(id)
    form = get_options(question)

    return render_template("questions/question.html",
                           question=question,
                           form=form)


@app.route("/study/<id>/question/new", methods=["GET", "POST"])
@login_required
def new_question(id):
    study = Study.query.get(id)
    q_count = db.session.query(Question).filter(Question.study == study).count()
    q_pos = q_count + 1
    form = QuestionForm()
    form.q_type.choices = [(q.display, q.name)
                           for q in QuestionType.query.all()]

    form.q_type.choices = [(q.display, q.name)
                           for q in QuestionType.query.all()]

    if form.is_submitted():
        # set position counter to one for options
        i = 1
        # create empty list for options
        options = []

        # get options from form data and write to db
        # if range question type is selected
        if form.q_type.data == "scale_number":
            # iterates over ranges saved in form data
            for k, v in form.ranges.data[0].items():
                # skips over csrf_token
                if k != "csrf_token":
                    o = Option()
                    o.value = str(v)
                    o.label = str(k)
                    o.position = i

                    options.append(o)
                    i += 1

        # if option question type is selected
        if form.q_type.data in ["true_false", "likert_scale", "multiple_choice"]:
            # iterates over options saved in form data
            for data in form.options.data:
                o = Option()
                o.value = data["value"]
                o.label = data["label"]
                o.position = i

                options.append(o)
                i += 1

        type = QuestionType.query.filter_by(display=form.q_type.data).first()

        q = Question()
        q.title = form.text.data
        #q.description = form.description.data
        q.questiontype = type
        #q.interval = form.interval.data
        q.position = form.position.data
        q.study = Study.query.get(id)
        q.options.extend(options)

        # creates list to store all entities that will be added to db
        insert = options
        # add question to insert
        insert.append(q)

        # writes all inserts to db and refreshes entities with ids
        db.session.add_all(insert)
        db.session.commit()

        flash("Your question has been created.", "success")
        return redirect(url_for("study", id=id))

    return render_template("questions/new_question.html", form=form, q_pos=q_pos)


@app.route("/question/<id>/delete", methods=["GET", "POST"])
def delete_question(id):
    # get question
    question = Question.query.get_or_404(id)
    form = ConfirmationForm()

    if form.is_submitted():
        if form.submit.data:

            study_id = question.study.id

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

    # delete question
    # delete all related options and answers
