from .. import app, db
from ..forms import EvaluationForm
from ..models import Source, Evaluation
from flask import render_template, flash, redirect, url_for
import base64
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import load_only

@app.route('/evaluations')
def evaluations():
    """
    Renders a page displaying statistics and a sample of evaluations.

    Returns:
        Rendered HTML template for the evaluations page.
    """
    # Randomly selects one source that has not been evaluated and has progress status 1
    source = Source.query.filter(~Source.evaluation.has())\
                         .filter(Source.progress == 1)\
                         .options(load_only("id"))\
                         .first()    

    # Gets the count of sources that have been evaluated
    eval = Source.query.filter(Source.evaluation.has())\
                       .options(load_only("id"))\
                       .count()

    # Gets the count of all sources
    total = Source.query.options(load_only("id")).count()

    # Calculates the percentage of evaluated sources
    if eval != 0:
        pct = round(eval/total*100)
    else:
        pct = 0

    # Gets the count of positive evaluations
    status = Evaluation.query.filter(Evaluation.status == 1).count()

    # Gets the count of all evaluations
    s_total = Evaluation.query.count()

    # Calculates the percentage of positive evaluations
    if status != 0:
        s_pct = round(status/s_total*100)
    else:
        s_pct = 0

    # Randomly selects 10 comments from evaluations that are not empty
    comments = Evaluation.query.filter(Evaluation.comment != '')\
                               .limit(10)\
                               .all()    

    return render_template('evaluations/evaluations.html',
                           source=source,
                           eval=eval,
                           total=total,
                           pct=pct,
                           status=status,
                           s_total=s_total,
                           s_pct=s_pct,
                           comments=comments)

@app.route('/source/<id>/evaluation', methods=["GET", "POST"])
def evaluation(id):
    """
    Handles the evaluation of a specific source.

    Args:
        id (int): The ID of the source to be evaluated.

    Returns:
        Rendered HTML template for the evaluation page or redirects based on form submission.
    """
    # Retrieves the source from the database using the provided ID
    source = Source.query.get_or_404(id)
    form = EvaluationForm()

    # Retrieves all evaluations associated with the given source
    evals = Evaluation.query.filter(Evaluation.source == source).all()

    # Randomly selects the next unevaluated source
    next = Source.query.filter(~Source.evaluation.has())\
                       .first()

    # Sets the ID of the next unevaluated source if available
    if next:
        next_id = next.id

    # Renders a PDF file as an image if the source's MIME type is PDF
    pdf_file = None
    if "pdf" in source.mime_type:
        pdf_file = id + ".pdf"
        with open(pdf_file, "wb") as pdf:
            pdf.write(base64.b64decode(source.bin))

    if form.is_submitted():
        # Checks if the source has already been evaluated
        check = Evaluation.query.filter(Evaluation.source == source).first()

        # Displays a warning if already evaluated, otherwise saves the new evaluation to the database
        if check:
            print(check.id)
            flash('Feedback wurde bereits abgegeben.', 'warning')
        else:
            eval = Evaluation()
            eval.comment = form.comment.data
            eval.status = form.status.data
            eval.source_id = source.id

            # Adds the new evaluation to the database and commits the transaction
            db.session.add(eval)
            db.session.commit()

            flash('Danke für das Feedback!', 'info')

            # Redirects to the next evaluation or to the evaluations list if no more sources are available
            if next:
                return redirect(url_for("evaluation", id=next_id))
            else:
                return redirect(url_for("evaluations"))

    return render_template('evaluations/evaluation.html',
                           form=form,
                           source=source,
                           evals=evals,
                           pdf_file=pdf_file,
                           next_id=next_id)
