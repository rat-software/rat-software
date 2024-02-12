from .. import app, db
from app.models import Answer, Question, Result, Source, Serp
from ..forms import ExportForm
from flask import render_template, send_file, flash
from sqlalchemy.orm import load_only
from sqlalchemy.inspection import inspect
from flask_security import login_required, current_user
import pandas as pd
from datetime import datetime
from io import BytesIO

table_styler = {"classes": "table table-hover",
                "index": False,
                "justify": "left",
                "border": 0}

@app.route('/<id>/export', methods=['GET', 'POST'])
@login_required
def export(id):
    form = ExportForm()

    tables = {}
    tables[0] = ["Assessments", Answer]
    tables[1] = ["Questions", Question]
    tables[2] = ["Search Results", Result]

    form.tables.choices = [(k, v[0]) for k, v in tables.items()]

    if form.is_submitted():
        label = tables[form.tables.data][0]
        model = tables[form.tables.data][1]

        sql = {}
        df = {}
        html = {}

        #sql[label] = model.query.filter(model.study_id == id).statement
        sql[label] = db.session.query(model).filter(model.study_id == id).statement
        df[label] = pd.read_sql(sql[label], db.session.bind)
        html[label] = df[label][:3].to_html(**table_styler)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, data in df.items():
                data.to_excel(writer, sheet_name=sheet)
        output.seek(0)

        filename = "%s_%s_%s.xlsx" % (id, label, datetime.now().strftime('%Y_%m_%d'))

        return send_file(output, attachment_filename=filename, as_attachment=True)

    return render_template('exports/assessment_export.html',
                           form=form, id=id)
