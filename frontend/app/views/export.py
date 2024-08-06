from .. import app, db
from app.models import Answer, Question, Result, Source, Serp
from ..forms import ExportForm
from flask import Blueprint, render_template, send_file, flash
from sqlalchemy.orm import load_only
from sqlalchemy.inspection import inspect
from flask_security import login_required, current_user
import pandas as pd
from datetime import datetime
from io import BytesIO
from sqlalchemy import create_engine
from sqlalchemy import text


#bp = Blueprint('export', __name__)

table_styler = {"classes": "table table-hover",
                "index": False,
                "justify": "left",
                "border": 0}

@app.route('/<id>/export', methods=['GET', 'POST'])
@login_required
def export(id):
    form = ExportForm()
    engine = db.session.get_bind()

    tables = {}
    tables[0] = ["Assessments", Answer]
    tables[1] = ["Questions", Question]
    tables[2] = ["Search Results", Result]

    form.tables.choices = [(k, v[0]) for k, v in tables.items()]

    if form.is_submitted():
        label = tables[form.tables.data][0]
        model = tables[form.tables.data][1]

        df = {}
        html = {}

        # Construct the SQL query with parameter binding
        query = db.session.query(model).filter(model.study_id == id).statement

        # Use SQLAlchemy's `text` object to safely pass parameters
        compiled_query = query.compile(engine, compile_kwargs={"literal_binds": True})

        # Execute the query and load the result into a DataFrame
        df[label] = pd.read_sql_query(compiled_query, engine)

        html[label] = df[label][:3].to_html(**table_styler)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet, data in df.items():
                data.to_excel(writer, sheet_name=sheet)
        output.seek(0)

        filename = "%s_%s_%s.xlsx" % (id, label, datetime.now().strftime('%Y_%m_%d'))

        return send_file(output, download_name=filename, as_attachment=True)

    return render_template('exports/assessment_export.html',
                           form=form, id=id)
