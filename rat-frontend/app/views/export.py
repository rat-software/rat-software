from .. import app, db
from app.models import (Study, Answer, Question, Result, Participant, ClassifierResult, 
                        Classifier, ClassifierIndicator, participant_study, Option, ResultAi, ResultChatbot, ResultAiSource, Serp)
from .analysis_func import (get_result_stats, get_evaluation_stats, get_classifier_stats, 
                           get_top_main_domains, get_answer_stats, convert_answer_stats_to_df)
from ..forms import ExportForm
from flask import request, Blueprint, render_template, send_file, flash
from flask_security import login_required
import pandas as pd
from datetime import datetime
from io import BytesIO
from sqlalchemy import text
import re

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

    # --- Python-Driven Mapping Dictionary (Loop Resolution Technique) ---
    query_map = {}
    try:
        queries = db.session.execute(text("SELECT id, query FROM query WHERE study = :study_id"), {'study_id': id}).all()
        for q_id, q_text in queries:
            query_map[q_id] = q_text
    except Exception:
        queries = db.session.execute(text("SELECT id, query FROM query WHERE study_id = :study_id"), {'study_id': id}).all()
        for q_id, q_text in queries:
            query_map[q_id] = q_text

    serp_to_query = {}
    try:
        pairs = db.session.execute(text("SELECT serp, query FROM result WHERE study = :study_id AND serp IS NOT NULL"), {'study_id': id}).all()
        for r_serp, r_query in pairs:
            if r_serp: serp_to_query[r_serp] = r_query
    except Exception:
        pairs = db.session.execute(text("SELECT serp_id, query FROM result WHERE study = :study_id AND serp_id IS NOT NULL"), {'study_id': id}).all()
        for r_serp, r_query in pairs:
            if r_serp: serp_to_query[r_serp] = r_query

    def get_assessments_df():
        """ Creates a DataFrame for ALL assessments and fills missing query keys using Python mapping. """
        has_participants = db.session.query(Participant.id).join(participant_study).filter(participant_study.c.study == id).first() is not None
        
        participant_col = "p.name AS participant_name," if has_participants else ""
        
        types_with_labels = ('true_false', 'likert_scale', 'multiple_choice')
        types_with_labels_sql_string = ", ".join([f"'{val}'" for val in types_with_labels])

        base_columns = f"""
            {participant_col}
            q.title AS question_title,
            q.position AS question_position,
            qt.name AS question_type,
            CASE
                WHEN qt.name IN ({types_with_labels_sql_string}) THEN COALESCE(o.label, a.value)
                ELSE a.value
            END AS answer,
            COALESCE(a.status, 0) AS assessment_status,
            a.created_at
        """

        # Block 1: Standard Results
        query_results = f"""
            SELECT
                qry.id AS query_id,
                qry.query AS query_string,
                'Search Result' AS source_type,
                r.title AS source_title,
                r.position AS source_position,
                NULL AS serp_page,
                r.main AS source_domain,
                r.url AS source_url,
                r.id AS source_id,
                {base_columns}
            FROM answer a
            JOIN result r ON a.result = r.id
            LEFT JOIN query qry ON r.query = qry.id
            JOIN question q ON a.question = q.id
            LEFT JOIN participant p ON a.participant = p.id
            LEFT JOIN option o ON a.question = o.question AND a.value = o.value
            LEFT JOIN questiontype qt ON q.question_type = qt.id
            WHERE a.study = :study_id AND a.result IS NOT NULL AND a.result_serp IS NULL
        """

        # Block 2: Granular SERP Results
        query_serps = f"""
            SELECT
                NULL AS query_id,
                NULL AS query_string,
                COALESCE(a.result_type_text, 'SERP Result') AS source_type,
                'SERP Layout' AS source_title,
                NULL AS source_position,
                COALESCE(s.page, 1) AS serp_page,
                NULL AS source_domain,
                NULL AS source_url,
                s.id AS source_id,
                {base_columns}
            FROM answer a
            JOIN serp s ON a.result_serp = s.id  
            JOIN question q ON a.question = q.id
            LEFT JOIN participant p ON a.participant = p.id
            LEFT JOIN option o ON a.question = o.question AND a.value = o.value
            LEFT JOIN questiontype qt ON q.question_type = qt.id
            WHERE a.study = :study_id
        """

        # Block 3: AI Overviews
        query_ai = f"""
            SELECT
                qry.id AS query_id,
                qry.query AS query_string,
                'AI Overview' AS source_type,
                'AI Answer' AS source_title,
                NULL AS source_position,
                NULL AS serp_page,
                NULL AS source_domain,
                NULL AS source_url,
                ra.id AS source_id,
                {base_columns}
            FROM answer a
            JOIN result_ai ra ON a.result_ai = ra.id
            LEFT JOIN query qry ON ra.query = qry.id  
            JOIN question q ON a.question = q.id
            LEFT JOIN participant p ON a.participant = p.id
            LEFT JOIN option o ON a.question = o.question AND a.value = o.value
            LEFT JOIN questiontype qt ON q.question_type = qt.id
            WHERE a.study = :study_id
        """

        # Block 4: Chatbots
        query_chatbot = f"""
            SELECT
                qry.id AS query_id,
                qry.query AS query_string,
                'Chatbot' AS source_type,
                'Chatbot Answer' AS source_title,
                NULL AS source_position,
                NULL AS serp_page,
                NULL AS source_domain,
                NULL AS source_url,
                rc.id AS source_id,
                {base_columns}
            FROM answer a
            JOIN result_chatbot rc ON a.result_chatbot = rc.id
            LEFT JOIN query qry ON rc.query = qry.id  
            JOIN question q ON a.question = q.id
            LEFT JOIN participant p ON a.participant = p.id
            LEFT JOIN option o ON a.question = o.question AND a.value = o.value
            LEFT JOIN questiontype qt ON q.question_type = qt.id
            WHERE a.study = :study_id
        """

        sql_query = text(f"""
            SELECT * FROM (
                {query_results} UNION ALL {query_serps} UNION ALL {query_ai} UNION ALL {query_chatbot}
            ) AS combined
            ORDER BY source_id, question_position
        """)

        if has_participants:
            labels = [
                'Query ID', 'Keyword (Query)', 'Source Type', 'Source Title', 'Source Position', 'SERP Page', 'Source Domain', 'Source URL', 
                'Source ID', 'Participant Name', 'Question', 'Question Position', 'Question Type', 'Answer', 'Status Code', 'Timestamp'
            ]
        else:
            labels = [
                'Query ID', 'Keyword (Query)', 'Source Type', 'Source Title', 'Source Position', 'SERP Page', 'Source Domain', 'Source URL', 
                'Source ID', 'Question', 'Question Position', 'Question Type', 'Answer', 'Status Code', 'Timestamp'
            ]

        params = {'study_id': id}
        records = db.session.execute(sql_query, params).all()
        df = pd.DataFrame.from_records(records, columns=labels).drop_duplicates()

        if not df.empty:
            for idx, row in df.iterrows():
                if 'serp' in str(row['Source Type']).lower():
                    s_id = row['Source ID']
                    if s_id in serp_to_query:
                        q_id = serp_to_query[s_id]
                        df.at[idx, 'Query ID'] = q_id
                        df.at[idx, 'Keyword (Query)'] = query_map.get(q_id, '')
                    elif query_map:
                        fallback_q_id = list(query_map.keys())[0]
                        df.at[idx, 'Query ID'] = fallback_q_id
                        df.at[idx, 'Keyword (Query)'] = query_map[fallback_q_id]

        return df

    def get_search_results_df():
        """ Creates an independent DataFrame for ALL search results with tracking IDs. """
        sql_query = text("""
            SELECT 
                r.id AS result_id, 
                q.id AS query_id, 
                q.query AS keyword, 
                r.engine_text AS searchengine, 
                r.title, 
                r.description, 
                r.url, 
                r.main, 
                r.position, 
                r.ip, 
                r.created_at 
            FROM result r 
            LEFT JOIN query q ON r.query = q.id 
            WHERE r.study = :study_id 
            ORDER BY q.id, r.position
        """)
        labels = ['Result ID', 'Query ID', 'Keyword', 'Search Engine', 'Title', 'Description', 'URL', 'Main', 'Position', 'IP', 'Timestamp']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels).drop_duplicates()

    def get_serp_results_master_df():
        """ Standalone clean worksheet for tracking SERP entities via Python lookup loop. """
        try:
            serp_records = db.session.execute(text("SELECT id, page, created_at FROM serp WHERE study = :study_id"), {'study_id': id}).all()
        except Exception:
            serp_records = db.session.execute(text("SELECT id, page, created_at FROM serp WHERE study_id = :study_id"), {'study_id': id}).all()

        master_rows = []
        for s_row in serp_records:
            s_id = s_row[0]
            page = s_row[1]
            created_at = s_row[2]
            
            q_id = serp_to_query.get(s_id, None)
            keyword = query_map.get(q_id, '') if q_id else ''
            
            if not q_id and query_map:
                q_id = list(query_map.keys())[0]
                keyword = query_map[q_id]

            master_rows.append({
                'Query ID': q_id,
                'Keyword': keyword,
                'SERP Tracking ID': s_id,
                'SERP Page': page,
                'Timestamp': created_at
            })

        return pd.DataFrame(master_rows).drop_duplicates()

    def get_classifier_results_df():
        sql_query = text("""
            SELECT 
                cr.id AS classifier_result_id, 
                r.id AS result_id, 
                cr.classifier AS classifier_id,
                r.url, 
                r.main, 
                c.display_name AS classifier_name, 
                cr.value, 
                cr.created_at 
            FROM classifier_result cr 
            JOIN result r ON cr.result = r.id 
            JOIN classifier c ON cr.classifier = c.id 
            WHERE r.study = :study_id 
            ORDER BY r.id, c.id
        """)
        labels = ['Classifier Result ID', 'Result ID', 'Classifier ID', 'URL', 'Main', 'Classifier', 'Value', 'Timestamp']
        return pd.DataFrame.from_records(db.session.execute(sql_query, {'study_id': id}).all(), columns=labels).drop_duplicates()

    def get_classifier_indicators_df():
        """ 
        Fixed master tab displaying the classifier indicators raw parameter values. 
        Includes the Classifier ID to allow for easy VLOOKUP filtering.
        """
        sql_query = text("""
            SELECT 
                ci.id AS indicator_result_id,
                ci.classifier AS classifier_id,       -- Added: Unique Classifier ID from table column
                r.id AS result_id,
                r.url,
                c.display_name AS classifier_name,
                ci.indicator AS indicator_key,
                ci.value AS indicator_value,
                ci.created_at
            FROM classifier_indicator ci
            JOIN result r ON ci.result = r.id
            JOIN classifier c ON ci.classifier = c.id
            WHERE r.study = :study_id
            ORDER BY r.id, c.id, ci.id
        """)
        # Aligned the labels array to capture the newly added column element seamlessly
        labels = ['Indicator Result ID', 'Classifier ID', 'Result ID', 'URL', 'Classifier Name', 'Indicator Parameter', 'Value', 'Timestamp']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels).drop_duplicates()

    def get_ai_results_df():
        """ Generates AI overview metrics including structural row tracking identifiers. """
        sql_query = text("""
            SELECT 
                ra.id AS ai_result_id, 
                q.query AS keyword, 
                ra.answer, 
                ra.created_at 
            FROM result_ai ra 
            JOIN query q ON ra.query = q.id 
            WHERE ra.study = :study_id 
            ORDER BY ra.created_at
        """)
        labels = ['AI Result ID', 'Keyword (Query)', 'Answer Text', 'Timestamp']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)

    def get_chatbot_results_df():
        """ Generates chatbot output details including structural row tracking identifiers. """
        sql_query = text("""
            SELECT 
                rc.id AS chatbot_result_id, 
                q.query AS keyword, 
                rc.answer, 
                rc.created_at 
            FROM result_chatbot rc 
            JOIN query q ON rc.query = q.id 
            WHERE rc.study = :study_id 
            ORDER BY rc.created_at
        """)
        labels = ['Chatbot Result ID', 'Keyword (Query)', 'Answer Text', 'Timestamp']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)

    def get_ai_sources_df():
        sql_query = text("SELECT ras.result_ai, ras.title, ras.description, ras.url, ras.position, ras.main FROM result_ai_source ras WHERE ras.study = :study_id ORDER BY ras.result_ai, ras.position")
        labels = ['AI Result ID', 'Title', 'Description', 'URL', 'Position', 'Main']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)
    
    def format_domain_df(domain_data, data_key):
        if not domain_data or data_key not in domain_data: return pd.DataFrame()
        df = pd.DataFrame(domain_data[data_key])
        if df.empty: return pd.DataFrame()
        df['percentage'] = df['percentage'].apply(lambda x: f"{x:.2f}%")
        if 'avg_position' in df.columns:
            df['avg_position'] = df['avg_position'].apply(lambda x: f"{x:.2f}" if x is not None else 'N/A')
        df.rename(columns={'percentage': 'Share of Total', 'avg_position': 'Avg. Position'}, inplace=True)
        return df

    def get_top_domains_standard_df():
        data = get_top_main_domains(study, limit=None)
        return format_domain_df(data, 'standard_results') if data else pd.DataFrame()

    def get_top_domains_ai_df():
        data = get_top_main_domains(study, limit=None)
        return format_domain_df(data, 'ai_sources') if data else pd.DataFrame()

    top_domains_preview = get_top_main_domains(study, limit=1)
    
    available_data = {
        'assessments': db.session.query(Answer).filter(Answer.study_id == id).first() is not None,
        'questions': db.session.query(Question).filter(Question.study_id == id).first() is not None,
        'search_results': db.session.query(Result).filter(Result.study_id == id).first() is not None,
        'serp_results_master': db.session.query(Serp).filter(Serp.study_id == id).first() is not None, 
        'classifier_results': db.session.query(ClassifierResult.id).join(Result).filter(Result.study_id == id).first() is not None,
        'classifier_indicators': db.session.query(ClassifierIndicator.id).join(Result).filter(Result.study_id == id).first() is not None,
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
            'serp_results_master': ("SERP Results Master", get_serp_results_master_df), 
            'ai_results': ("AI Overview Results", get_ai_results_df),
            'chatbot_results': ("Chatbot Results", get_chatbot_results_df),
            'ai_sources': ("AI Overview Sources", get_ai_sources_df),
            'classifier_results': ("Classifier Results", get_classifier_results_df),
            'classifier_indicators': ("Classifier Indicators", get_classifier_indicators_df),
            'questions': ("Questions", lambda: pd.read_sql_query(db.session.query(Question).filter(Question.study_id == id).statement, engine))
        }
        
        for key, (label, func) in export_options.items():
            if available_data.get(key, False):
                df = func()
                if not df.empty:
                    df.to_excel(writer, sheet_name=label, index=False)
        
        writer.close()
        output.seek(0)

        safe_study_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', study.name)
        
        filename = f"study_{id}_{safe_study_name}_full_report_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        
        return send_file(output, download_name=filename, as_attachment=True)

    return render_template('exports/assessment_export.html',
                           form=form,
                           id=id,
                           available_data=available_data)