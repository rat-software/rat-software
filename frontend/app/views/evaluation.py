from .. import app, db
from ..forms import EvaluationForm
from ..models import Source, Evaluation
from flask import render_template, flash, redirect, url_for
import base64
from sqlalchemy.sql.expression import func
from sqlalchemy.orm import load_only


@app.route('/evaluations')
def evaluations():
    # randomly selects one not evaluated source
    source = Source.query.filter(~Source.evaluation.has())\
                         .filter(Source.progress == 1)\
                         .options(load_only("id"))\
                         .order_by(func.random())\
                         .first()

    # gets count of evaluated sources
    eval = Source.query.filter(Source.evaluation.has())\
                       .options(load_only("id"))\
                       .count()

    # gets count of all sources
    total = Source.query.options(load_only("id")).count()

    # calculates percentage of evaluated sources
    if eval != 0:
        pct = round(eval/total*100)
    else:
        pct = 0

    # gets count of positive evaluations
    status = Evaluation.query.filter(Evaluation.status == 1).count()

    # gets count of all evaluations
    s_total = Evaluation.query.count()

    # calculates percentage of positive evaluations
    if status != 0:
        s_pct = round(status/s_total*100)
    else:
        s_pct = 0

    # randomly gets 10 comments from evaluations
    comments = Evaluation.query.filter(Evaluation.comment != '')\
                               .order_by(func.random())\
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
    # gets source from db
    source = Source.query.get_or_404(id)
    form = EvaluationForm()

    # gets evaluations from db
    evals = Evaluation.query.filter(Evaluation.source == source).all()

    # randomly gets next unevaluated source
    next = Source.query.filter(~Source.evaluation.has())\
                       .order_by(func.random())\
                       .first()

    # sets next_id if one unevaluated source is found
    if next:
        next_id = next.id

    # renders pdf as image
    pdf_file = None
    if "pdf" in source.mime_type:
        pdf_file = id+".pdf"
        with open(pdf_file, "wb") as pdf:
            pdf.write(base64.b64decode(source.bin))

    if form.is_submitted():
        # check if source has been evaluated before
        check = Evaluation.query.filter(Evaluation.source == source).first()

        # if already evaluated => notification
        # else => save evaluation to db
        if check:
            print(check.id)
            flash('Feedback wurde bereits abgegeben.', 'warning')
        else:
            eval = Evaluation()
            eval.comment = form.comment.data
            eval.status = form.status.data
            eval.source_id = source.id

            # writes evaluation to db
            db.session.add(eval)
            db.session.commit()

            flash('Danke für das Feedback!', 'info')

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
