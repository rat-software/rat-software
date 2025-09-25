# HINWEIS: Stelle sicher, dass diese Imports am Anfang der Datei korrekt sind.
from .. import app, db
from app.models import (Study, Answer, Question, Result, Participant, ClassifierResult, 
                        Classifier, participant_study, Option, ResultAi, ResultChatbot, ResultAiSource)
from .analysis_func import (get_result_stats, get_evaluation_stats, get_classifier_stats, 
                           get_top_main_domains, get_answer_stats, convert_answer_stats_to_df)
from ..forms import ExportForm
from flask import request, Blueprint, render_template, send_file, flash
from flask_security import login_required
import pandas as pd
from datetime import datetime
from io import BytesIO
from sqlalchemy import text

@app.route('/<id>/export', methods=['GET', 'POST'])
@login_required
def export(id):
    """
    Handles the dynamic export of data and analysis from the database into an Excel file.
    """
    form = ExportForm()
    engine = db.session.get_bind()
    
    study = db.session.query(Study).filter(Study.id == id).first_or_404()
    result_stats_data = get_result_stats(study)
    evaluation_stats_data = get_evaluation_stats(study)
    classifier_stats_data = get_classifier_stats(study)
    answer_stats_data = get_answer_stats(study)

    # ==============================================================================
    # HILFSFUNKTIONEN
    # ==============================================================================
    
    def get_assessments_df():
        """ Erstellt ein DataFrame für ALLE Assessments (Suchergebnisse, AI Overviews, Chatbots). """
        has_participants = db.session.query(Participant.id).join(participant_study).filter(participant_study.c.study == id).first() is not None
        
        types_with_labels = ('true_false', 'likert_scale', 'multiple_choice')
        types_with_labels_sql_string = ", ".join([f"'{val}'" for val in types_with_labels])

        base_columns = """
            p.name AS participant_name,
            q.title AS question_title,
            q.position AS question_position,
            qt.name AS question_type,
            CASE
                WHEN qt.name IN ({}) THEN COALESCE(o.label, a.value)
                ELSE a.value
            END AS answer,
            a.created_at
        """.format(types_with_labels_sql_string)

        query_results = f"""
            SELECT
                'Search Result' AS source_type,
                r.url AS source_url,
                r.id AS source_id,
                {base_columns}
            FROM answer a
            JOIN result r ON a.result = r.id
            JOIN question q ON a.question = q.id
            LEFT JOIN participant p ON a.participant = p.id
            LEFT JOIN option o ON a.question = o.question AND a.value = o.value
            LEFT JOIN questiontype qt ON q.question_type = qt.id
            WHERE a.study = :study_id AND a.result IS NOT NULL
        """

        query_ai = f"""
            SELECT
                'AI Overview' AS source_type,
                qry.query AS source_url,
                ra.id AS source_id,
                {base_columns}
            FROM answer a
            JOIN result_ai ra ON a.result_ai = ra.id
            JOIN query qry ON ra.query = qry.id
            JOIN question q ON a.question = q.id
            LEFT JOIN participant p ON a.participant = p.id
            LEFT JOIN option o ON a.question = o.question AND a.value = o.value
            LEFT JOIN questiontype qt ON q.question_type = qt.id
            WHERE a.study = :study_id AND a.result_ai IS NOT NULL
        """

        query_chatbot = f"""
            SELECT
                'Chatbot' AS source_type,
                qry.query AS source_url,
                rc.id AS source_id,
                {base_columns}
            FROM answer a
            JOIN result_chatbot rc ON a.result_chatbot = rc.id
            JOIN query qry ON rc.query = qry.id
            JOIN question q ON a.question = q.id
            LEFT JOIN participant p ON a.participant = p.id
            LEFT JOIN option o ON a.question = o.question AND a.value = o.value
            LEFT JOIN questiontype qt ON q.question_type = qt.id
            WHERE a.study = :study_id AND a.result_chatbot IS NOT NULL
        """

        if has_participants:
            sql_query = text(f"""
                {query_results} UNION ALL {query_ai} UNION ALL {query_chatbot}
                ORDER BY participant_name, source_id, question_position
            """)
            labels = ['Source Type', 'Source URL/Query', 'Source ID', 'Participant Name', 'Question', 'Question Position', 'Question Type', 'Answer', 'Timestamp']
        else:
            sql_query = text(f"""
                SELECT * FROM (
                    {query_results.replace('p.name AS participant_name,', '')} UNION ALL
                    {query_ai.replace('p.name AS participant_name,', '')} UNION ALL
                    {query_chatbot.replace('p.name AS participant_name,', '')}
                ) AS combined
                ORDER BY source_id, question_position
            """)
            labels = ['Source Type', 'Source URL/Query', 'Source ID', 'Question', 'Question Position', 'Question Type', 'Answer', 'Timestamp']

        params = {'study_id': id}
        records = db.session.execute(sql_query, params).all()
        return pd.DataFrame.from_records(records, columns=labels).drop_duplicates()

    def get_search_results_df():
        """ Erstellt ein DataFrame für die Suchergebnisse. """
        sql_query = text("SELECT se.name AS searchengine, r.title, r.description, r.url, r.main, r.position, r.ip, r.created_at FROM result r JOIN scraper s ON r.scraper = s.id JOIN searchengine se ON s.searchengine = se.id WHERE r.study = :study_id ORDER BY s.id, r.position")
        return pd.DataFrame.from_records(db.session.execute(sql_query, {'study_id': id}).all(), columns=['Search Engine', 'Title', 'Description', 'URL', 'Main', 'Position', 'IP', 'Timestamp']).drop_duplicates()

    def get_classifier_results_df():
        """ Erstellt ein DataFrame für die Classifier-Ergebnisse (Rohdaten). """
        sql_query = text("SELECT r.url, r.main, c.display_name AS classifier_name, cr.value, cr.created_at FROM classifier_result cr JOIN result r ON cr.result = r.id JOIN classifier c ON cr.classifier = c.id WHERE r.study = :study_id ORDER BY r.id, c.id")
        return pd.DataFrame.from_records(db.session.execute(sql_query, {'study_id': id}).all(), columns=['URL', 'Main', 'Classifier', 'Value', 'Timestamp']).drop_duplicates()

    def get_ai_results_df():
        """ Erstellt ein DataFrame für die AI Overview Ergebnisse. """
        sql_query = text("SELECT q.query, ra.answer, ra.created_at FROM result_ai ra JOIN query q ON ra.query = q.id WHERE ra.study = :study_id ORDER BY ra.created_at")
        labels = ['Query', 'Answer', 'Timestamp']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)

    def get_chatbot_results_df():
        """ Erstellt ein DataFrame für die Chatbot Ergebnisse. """
        sql_query = text("SELECT q.query, rc.answer, rc.created_at FROM result_chatbot rc JOIN query q ON rc.query = q.id WHERE rc.study = :study_id ORDER BY rc.created_at")
        labels = ['Query', 'Answer', 'Timestamp']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)

    def get_ai_sources_df():
        """ Erstellt ein DataFrame für die Quellen der AI Overviews. """
        sql_query = text("SELECT ras.result_ai, ras.title, ras.description, ras.url, ras.position, ras.main FROM result_ai_source ras WHERE ras.study = :study_id ORDER BY ras.result_ai, ras.position")
        labels = ['AI Result ID', 'Title', 'Description', 'URL', 'Position', 'Main']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)
    
    def format_domain_df(domain_data, data_key):
        """ Formatiert die Top-Domain-DataFrames für den Export. """
        if not domain_data or data_key not in domain_data: return pd.DataFrame()
        df = pd.DataFrame(domain_data[data_key])
        df['percentage'] = df['percentage'].apply(lambda x: f"{x:.2f}%")
        if 'avg_position' in df.columns:
            df['avg_position'] = df['avg_position'].apply(lambda x: f"{x:.2f}" if x is not None else 'N/A')
        df.rename(columns={'percentage': 'Share of Total', 'avg_position': 'Avg. Position'}, inplace=True)
        return df

    def get_top_domains_standard_df():
        """ Ruft ALLE Standard-Domains für den Export ab. """
        data = get_top_main_domains(study, limit=None)
        return format_domain_df(data, 'standard_results') if data else pd.DataFrame()

    def get_top_domains_ai_df():
        """ Ruft ALLE AI-Source-Domains für den Export ab. """
        data = get_top_main_domains(study, limit=None)
        return format_domain_df(data, 'ai_sources') if data else pd.DataFrame()

    # --- Verfügbarkeit von Daten prüfen ---
    top_domains_preview = get_top_main_domains(study, limit=1)
    available_data = {
        'assessments': db.session.query(Answer).filter(Answer.study_id == id).first() is not None,
        'questions': db.session.query(Question).filter(Question.study_id == id).first() is not None,
        'search_results': db.session.query(Result).filter(Result.study_id == id).first() is not None,
        'classifier_results': db.session.query(ClassifierResult.id).join(Result).filter(Result.study_id == id).first() is not None,
        'ai_results': db.session.query(ResultAi).filter(ResultAi.study_id == id).first() is not None,
        'chatbot_results': db.session.query(ResultChatbot).filter(ResultChatbot.study_id == id).first() is not None,
        'ai_sources': db.session.query(ResultAiSource).filter(ResultAiSource.study_id == id).first() is not None,
        'result_stats': bool(result_stats_data),
        'evaluation_stats': bool(evaluation_stats_data),
        'evaluation_breakdown': bool(evaluation_stats_data and 'breakdown' in evaluation_stats_data),
        'classifier_stats': bool(classifier_stats_data),
        'top_domains_standard': bool(top_domains_preview and 'standard_results' in top_domains_preview),
        'top_domains_ai': bool(top_domains_preview and 'ai_sources' in top_domains_preview),
        'answer_stats': bool(answer_stats_data),
    }
    
    # ==============================================================================
    # HAUPTLOGIK
    # ==============================================================================
    if request.method == 'POST':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        export_options = {
            'result_stats': ("Result Stats", lambda: pd.DataFrame(list(result_stats_data.items()), columns=['Statistic', 'Value'])),
            'evaluation_stats': ("Evaluation Stats", lambda: pd.DataFrame([s for s in evaluation_stats_data.items() if s[0] != 'breakdown'], columns=['Statistic', 'Value'])),
            'evaluation_breakdown': ("Evaluation Breakdown", lambda: pd.DataFrame(evaluation_stats_data['breakdown']) if evaluation_stats_data and 'breakdown' in evaluation_stats_data else pd.DataFrame()),
            'answer_stats': ("Answer Stats", lambda: convert_answer_stats_to_df(answer_stats_data)),
            'classifier_stats': ("Classifier Stats", lambda: pd.DataFrame([{'Classifier': cls, 'Value': val, 'Count': data['count'], 'Percentage of Total': f"{data['percentage']:.2f}%"} for cls, values in classifier_stats_data.items() for val, data in values.get('raw_stats', {}).items()]) if classifier_stats_data else pd.DataFrame()),
            'top_domains_standard': ("All Domains (Standard)", get_top_domains_standard_df),
            'top_domains_ai': ("All Domains (AI Sources)", get_top_domains_ai_df),
            'assessments': ("Assessments", get_assessments_df),
            'search_results': ("Search Results", get_search_results_df),
            'ai_results': ("AI Overview Results", get_ai_results_df),
            'chatbot_results': ("Chatbot Results", get_chatbot_results_df),
            'ai_sources': ("AI Overview Sources", get_ai_sources_df),
            'classifier_results': ("Classifier Results", get_classifier_results_df),
            'questions': ("Questions", lambda: pd.read_sql_query(db.session.query(Question).filter(Question.study_id == id).statement, engine))
        }
        
        for key, (label, func) in export_options.items():
            if available_data.get(key, False):
                df = func()
                if not df.empty:
                    df.to_excel(writer, sheet_name=label, index=False)
        
        writer.close()
        output.seek(0)
        filename = f"study_{id}_full_report_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        return send_file(output, download_name=filename, as_attachment=True)

    return render_template('exports/assessment_export.html',
                           form=form,
                           id=id,
                           available_data=available_data)