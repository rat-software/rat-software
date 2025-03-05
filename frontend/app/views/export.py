from .. import app, db
from app.models import Answer, Question, Result, Source, Serp, Query, ClassifierResult
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
import os


#bp = Blueprint('export', __name__)

# Define styling options for the HTML table
table_styler = {"classes": "table table-hover",
                "index": False,
                "justify": "left",
                "border": 0}

@app.route('/<id>/export', methods=['GET', 'POST'])
@login_required
def export(id):
    """
    Handles the export of data from the database into an Excel file.

    Args:
        id (int): The ID of the study for which to export data.

    Returns:
        Renders the export form or sends an Excel file as an attachment if the form is submitted.
    """
    form = ExportForm()
    engine = db.session.get_bind()

    # Define table models to be exported
    tables = {}
    tables[0] = ["Assessments", Answer]
    tables[1] = ["Questions", Question]
    tables[2] = ["Search Results", Result]
    tables[3] = ["Classifier", ClassifierResult]

    # Populate the choices for the export form
    form.tables.choices = [(k, v[0]) for k, v in tables.items()]

    if form.is_submitted():
        # Get the selected table label and model
        label = tables[form.tables.data][0]
        model = tables[form.tables.data][1]

        df = {}
        html = {}
        
        if "Classifier" in label:

            query = db.session.execute(text("SELECT result.id, result.url, result.main, classifier.display_name, classifier_result.value, classifier_result.created_at FROM classifier_result JOIN classifier ON classifier.id = classifier_result.classifier JOIN result ON classifier_result.result = result.id JOIN classifier_study ON result.study = classifier_study.study JOIN classifier_study AS cs_check ON cs_check.study = classifier_study.study AND cs_check.classifier = classifier.id WHERE classifier_study.study = :id_study ORDER BY result.id, classifier.id"), {'id_study': str(id)}).all()
            labels = ['Id Result', 'URL', 'Main', 'Classifier', 'Value', 'Created At']
            df = pd.DataFrame.from_records(query, columns=labels)
            df = df.drop_duplicates()

            filename = "%s_%s_%s.xlsx" % (id, label, datetime.now().strftime('%Y_%m_%d'))
            current_directory = os.getcwd()
            path = current_directory + str(id) + filename
            df.to_excel(path)

            return send_file(path, as_attachment=True, download_name=filename)            

            
        # Construct the SQL query for the selected table with parameter binding
        else:
            query = db.session.query(model).filter(model.study_id == id).statement

            # Use SQLAlchemy's `text` object to safely compile the query with literal binds
            compiled_query = query.compile(engine, compile_kwargs={"literal_binds": True})

            # Execute the compiled query and load the result into a DataFrame
            df[label] = pd.read_sql_query(compiled_query, engine)

      
            # Convert the first few rows of the DataFrame to HTML for display (not used in this code)
            html[label] = df[label][:3].to_html(**table_styler)

           
            # Create an Excel file from the DataFrame
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                for sheet, data in df.items():
                    data.to_excel(writer, sheet_name=sheet)
            output.seek(0)

            # Generate a filename for the Excel file
            filename = "%s_%s_%s.xlsx" % (id, label, datetime.now().strftime('%Y_%m_%d'))

            # Send the Excel file as an attachment
            return send_file(output, download_name=filename, as_attachment=True)


    # Render the export form if not submitted
    return render_template('exports/assessment_export.html',
                           form=form, id=id)
