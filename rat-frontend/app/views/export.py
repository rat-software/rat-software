from .. import app, db
from app.models import (Study, Answer, Question, Result, Participant, ClassifierResult, 
                        Classifier, ClassifierIndicator, participant_study, Option, ResultAi, ResultChatbot, ResultAiSource, Serp, ResultImage)
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
import json

@app.route('/<id>/export', methods=['GET', 'POST'])
@login_required
def export(id):
    """
    Handles the dynamic export of study data and analysis from the database into an Excel file.
    
    Extracts comprehensive metrics including participant assessments, survey responses, 
    SERP metadata, AI overview breakdowns, and automated classification outputs, packaging 
    them seamlessly into individual Excel sheets.
    
    Args:
        id (int/str): The unique identifier of the Study to export.
        
    Returns:
        Response: A binary spreadsheet file download on POST, or a rendered configuration 
                  HTML template on GET.
    """
    form = ExportForm()
    engine = db.session.get_bind()
    
    # Fetch base study properties and compute cached statistics
    study = db.session.query(Study).filter(Study.id == id).first_or_404()
    result_stats_data = get_result_stats(study)
    evaluation_stats_data = get_evaluation_stats(study)
    classifier_stats_data = get_classifier_stats(study)
    answer_stats_data = get_answer_stats(study)

    # --- Python-Driven Mapping Dictionary (Loop Resolution Technique) ---
    # Maps query IDs to their raw keyword strings to prevent expensive SQL JOIN loops later
    query_map = {}
    try:
        queries = db.session.execute(text("SELECT id, query FROM query WHERE study = :study_id"), {'study_id': id}).all()
        for q_id, q_text in queries:
            query_map[q_id] = q_text
    except Exception:
        # Fallback handling for variants in database schema layout (study vs study_id columns)
        queries = db.session.execute(text("SELECT id, query FROM query WHERE study_id = :study_id"), {'study_id': id}).all()
        for q_id, q_text in queries:
            query_map[q_id] = q_text

    # Maps SERP records back to their originating core search queries
    serp_to_query = {}
    try:
        pairs = db.session.execute(text("SELECT serp, query FROM result WHERE study = :study_id AND serp IS NOT NULL"), {'study_id': id}).all()
        for r_serp, r_query in pairs:
            if r_serp: serp_to_query[r_serp] = r_query
    except Exception:
        pairs = db.session.execute(text("SELECT serp_id, query FROM result WHERE study = :study_id AND serp_id IS NOT NULL"), {'study_id': id}).all()
        for r_serp, r_query in pairs:
            if r_serp: serp_to_query[r_serp] = r_query
            

    def get_study_metadata_df():
        """
        Creates a summary DataFrame with the study's core setup and operational metadata.
        
        Returns:
            pd.DataFrame: A two-column DataFrame containing configuration properties and values.
        """
        metadata = [
            {'Property': 'Study ID', 'Value': study.id},
            {'Property': 'Study Name', 'Value': study.name},
            {'Property': 'Description', 'Value': study.description or 'N/A'},
            {'Property': 'Task Description (shown to users)', 'Value': study.task or 'N/A'},
            {'Property': 'Study Introduction', 'Value': study.participant_description if study.show_description_after_join else 'Disabled'},
            {'Property': 'Live Link Mode', 'Value': 'Enabled' if study.live_link_mode else 'Disabled'},
            {'Property': 'Created At', 'Value': study.created_at.strftime('%Y-%m-%d %H:%M:%S') if study.created_at else 'N/A'}
        ]
        return pd.DataFrame(metadata)            
            

    def get_assessments_df():
        """
        Creates a structured DataFrame containing ALL user evaluation answers across all target modules.
        
        Executes a raw SQL UNION query combining human evaluation answers across standard search engine 
        results, distinct whole-page SERP layout configurations, AI summaries/overviews, and 
        interactive LLM Chatbot elements. Missing query relationships are dynamically fixed post-fetch.
        
        Returns:
            pd.DataFrame: A comprehensive matrix of questions, answers, source data, and user identifiers.
        """
        # Dynamically inspect if this study contains assigned participants to adapt column layouts
        has_participants = db.session.query(Participant.id).join(participant_study).filter(participant_study.c.study == id).first() is not None
        
        participant_col = "p.name AS participant_name," if has_participants else ""
        
        # Build relational resolution for closed-ended selectable options vs open-text input strings
        types_with_labels = ('true_false', 'likert_scale', 'multiple_choice', 'single_choice')
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

        # Block 1: Gather answers linked directly to classic standard Search Results
        query_results = f"""
            SELECT
                qry.id AS query_id,
                qry.query AS query_string,
                'Search Result' AS source_type,
                r.engine_text AS search_engine,
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

        # Block 2: Gather answers linked to custom overall Search Engine Results Page (SERP) layouts
        query_serps = f"""
            SELECT
                NULL AS query_id,
                NULL AS query_string,
                COALESCE(a.result_type_text, 'SERP Result') AS source_type,
                s.engine_text AS search_engine,
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

        # Block 3: Gather answers linked to integrated zero-click AI Overviews
        query_ai = f"""
            SELECT
                qry.id AS query_id,
                qry.query AS query_string,
                'AI Overview' AS source_type,
                ra.engine_text AS search_engine,
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

        # Block 4: Gather answers linked to full standalone conversational Chatbots
        query_chatbot = f"""
            SELECT
                qry.id AS query_id,
                qry.query AS query_string,
                'Chatbot' AS source_type,
                rc.engine_text AS search_engine,
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

        query_image = f"""
            SELECT
                qry.id AS query_id,
                qry.query AS query_string,
                'Image Result' AS source_type,
                ri.engine_text AS search_engine,
                ri.title AS source_title,
                ri.position AS source_position,
                NULL AS serp_page,
                ri.source_name AS source_domain,
                ri.source_url AS source_url,
                ri.id AS source_id,
                {base_columns}
            FROM answer a
            JOIN result_image ri ON a.result_image = ri.id
            LEFT JOIN query qry ON ri.query = qry.id
            JOIN question q ON a.question = q.id
            LEFT JOIN participant p ON a.participant = p.id
            LEFT JOIN option o ON a.question = o.question AND a.value = o.value
            LEFT JOIN questiontype qt ON q.question_type = qt.id
            WHERE a.study = :study_id
        """
        sql_query = text(f"""
            SELECT * FROM (
                {query_results} UNION ALL {query_serps} UNION ALL {query_ai} UNION ALL {query_chatbot} UNION ALL {query_image}
            ) AS combined
            ORDER BY source_id, question_position
        """)


        if has_participants:
            labels = [
                'Query ID', 'Keyword (Query)', 'Source Type', 'Search Engine', 'Source Title', 'Source Position', 'SERP Page', 'Source Domain', 'Source URL', 
                'Source ID', 'Participant Name', 'Question', 'Question Position', 'Question Type', 'Answer', 'Status Code', 'Timestamp'
            ]
        else:
            labels = [
                'Query ID', 'Keyword (Query)', 'Source Type', 'Search Engine', 'Source Title', 'Source Position', 'SERP Page', 'Source Domain', 'Source URL', 
                'Source ID', 'Question', 'Question Position', 'Question Type', 'Answer', 'Status Code', 'Timestamp'
            ]

        params = {'study_id': id}
        records = db.session.execute(sql_query, params).all()
        df = pd.DataFrame.from_records(records, columns=labels).drop_duplicates()

        # Post-processing fallback: Fill missing Query data fields for disconnected SERP entries
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
        """
        Extracts a clean registry log containing every captured organic or paid search item result.
        
        Returns:
            pd.DataFrame: Registry list capturing metadata, titles, URLs, snippets, and positions.
        """
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
        """
        Builds a tracking record master log tracking page iteration snapshots.
        
        Returns:
            pd.DataFrame: Matrix parsing SERP page tracking keys, timestamps, and queries.
        """
        try:
            serp_records = db.session.execute(text("SELECT id, page, created_at, engine_text FROM serp WHERE study = :study_id"), {'study_id': id}).all()
        except Exception:
            serp_records = db.session.execute(text("SELECT id, page, created_at, engine_text FROM serp WHERE study_id = :study_id"), {'study_id': id}).all()

        master_rows = []
        for s_row in serp_records:
            s_id = s_row[0]
            page = s_row[1]
            created_at = s_row[2]
            engine_text = s_row[3]
            
            q_id = serp_to_query.get(s_id, None)
            keyword = query_map.get(q_id, '') if q_id else ''
            
            # Map structural edge case defaults where standalone logs lose link references
            if not q_id and query_map:
                q_id = list(query_map.keys())[0]
                keyword = query_map[q_id]

            master_rows.append({
                'Query ID': q_id,
                'Keyword': keyword,
                'Search Engine': engine_text,
                'SERP Tracking ID': s_id,
                'SERP Page': page,
                'Timestamp': created_at
            })

        return pd.DataFrame(master_rows).drop_duplicates()

    def get_classifier_results_df():
        sql_query = text("""
            SELECT 
                cr.id AS classifier_result_id, 
                c.display_name AS classifier_name, 
                cr.result AS result_id,
                cr.result_ai,
                cr.result_chatbot,
                cr.result_ai_source,
                cr.result_image,
                CASE 
                    WHEN cr.result IS NOT NULL THEN 'Organic Result'
                    WHEN cr.result_ai IS NOT NULL THEN 'AI Overview'
                    WHEN cr.result_chatbot IS NOT NULL THEN 'Chatbot'
                    WHEN cr.result_ai_source IS NOT NULL THEN 'AI Source'
                    WHEN cr.result_image IS NOT NULL THEN 'Image Result'
                    ELSE 'Unknown'
                END AS source_type,
                COALESCE(cr.result, cr.result_ai, cr.result_chatbot, cr.result_ai_source, cr.result_image) AS source_id,
                COALESCE(r.url, ras.url, ri.source_url) AS url, 
                cr.value, 
                cr.created_at 
            FROM classifier_result cr 
            JOIN classifier c ON cr.classifier = c.id 
            LEFT JOIN result r ON cr.result = r.id 
            LEFT JOIN result_ai ra ON cr.result_ai = ra.id
            LEFT JOIN result_chatbot rc ON cr.result_chatbot = rc.id
            LEFT JOIN result_ai_source ras ON cr.result_ai_source = ras.id
            LEFT JOIN result_image ri ON cr.result_image = ri.id
            WHERE cr.study = :study_id 
               OR r.study = :study_id 
               OR ra.study = :study_id 
               OR rc.study = :study_id 
               OR ras.study = :study_id
               OR ri.study = :study_id
            ORDER BY c.display_name, source_type, source_id
        """)
        labels = ['Classifier Result ID', 'Classifier', 'Result ID', 'Result AI', 'Result Chatbot', 'Result AI Source', 'Result Image', 'Source Type', 'Source ID', 'URL', 'Value', 'Timestamp']
        df = pd.DataFrame.from_records(db.session.execute(sql_query, {'study_id': id}).all(), columns=labels).drop_duplicates()

        # --- JSON UNPACKING LOGIC (Classifier Results) ---
        if not df.empty and 'Value' in df.columns:
            def extract_json_safe(val):
                if not isinstance(val, str): return {'Raw_Value': val}
                v = val.strip()
                
                # Excel protection: Truncate extremely long texts to prevent file corruption
                if len(v) > 30000:
                    v = v[:29900] + "... [Text truncated due to excessive length]"
                    
                if v.startswith("```"):
                    v = re.sub(r'^```[a-zA-Z]*\n?', '', v)
                    v = re.sub(r'\n?```$', '', v).strip()
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, dict): return parsed
                    return {'Raw_Value': v}
                except json.JSONDecodeError:
                    m = re.search(r'\{.*\}', v, re.DOTALL)
                    if m:
                        try:
                            parsed = json.loads(m.group(0))
                            if isinstance(parsed, dict): return parsed
                        except: pass
                # Not a JSON (e.g., Classic Classifier like Readability) -> Keep raw text
                return {'Raw_Value': v}

            try:
                parsed_list = df['Value'].apply(extract_json_safe).tolist()
                parsed_df = pd.json_normalize(parsed_list)
                parsed_df.index = df.index
                parsed_df = parsed_df.add_prefix('Value_')
                df = pd.concat([df.drop(columns=['Value']), parsed_df], axis=1)
            except Exception as e:
                pass

        return df

    def get_classifier_indicators_df():
        sql_query = text("""
            SELECT 
                ci.id AS indicator_result_id,
                c.display_name AS classifier_name,
                ci.result AS result_id,
                ci.result_ai,
                ci.result_chatbot,
                ci.result_ai_source,
                ci.result_image,
                CASE 
                    WHEN ci.result IS NOT NULL THEN 'Organic Result'
                    WHEN ci.result_ai IS NOT NULL THEN 'AI Overview'
                    WHEN ci.result_chatbot IS NOT NULL THEN 'Chatbot'
                    WHEN ci.result_ai_source IS NOT NULL THEN 'AI Source'
                    WHEN ci.result_image IS NOT NULL THEN 'Image Result'
                    ELSE 'Unknown'
                END AS source_type,
                COALESCE(ci.result, ci.result_ai, ci.result_chatbot, ci.result_ai_source, ci.result_image) AS source_id,
                COALESCE(r.url, ras.url, ri.source_url) AS url,
                ci.indicator AS indicator_key,
                ci.value AS indicator_value,
                ci.created_at
            FROM classifier_indicator ci
            JOIN classifier c ON ci.classifier = c.id
            LEFT JOIN result r ON ci.result = r.id
            LEFT JOIN result_ai ra ON ci.result_ai = ra.id
            LEFT JOIN result_chatbot rc ON ci.result_chatbot = rc.id
            LEFT JOIN result_ai_source ras ON ci.result_ai_source = ras.id
            LEFT JOIN result_image ri ON ci.result_image = ri.id
            WHERE ci.study = :study_id 
               OR r.study = :study_id 
               OR ra.study = :study_id 
               OR rc.study = :study_id 
               OR ras.study = :study_id
               OR ri.study = :study_id
            ORDER BY c.display_name, source_type, source_id
        """)
        labels = ['Indicator Result ID', 'Classifier Name', 'Result ID', 'Result AI', 'Result Chatbot', 'Result AI Source', 'Result Image', 'Source Type', 'Source ID', 'URL', 'Indicator Parameter', 'Value', 'Timestamp']
        df = pd.DataFrame.from_records(db.session.execute(sql_query, {'study_id': id}).all(), columns=labels).drop_duplicates()

        # --- JSON UNPACKING LOGIC (Indicators) ---
        if not df.empty and 'Value' in df.columns:
            try:
                # 1. Extract expected keys from the prompt
                task_expected_keys = {}
                if study.llm_classifiers_json:
                    try:
                        llm_tasks = json.loads(study.llm_classifiers_json)
                        for task in llm_tasks:
                            if not task.get('active', True): continue
                            d_name = task.get('display_name')
                            prompt_text = task.get('prompt', '')
                            if d_name and prompt_text:
                                json_block = re.search(r'\{.*\}', prompt_text, re.DOTALL)
                                if json_block:
                                    keys = re.findall(r'"([a-zA-Z0-9_-]+)"\s*:', json_block.group(0))
                                    if keys:
                                        task_expected_keys[d_name] = [k.lower() for k in keys]
                    except: pass
    
                parsed_list = []
                for index, row in df.iterrows():
                    val = row.get('Value')
                    ind_key = row.get('Indicator Parameter', '')
                    clean_name = str(ind_key).replace("LLM_", "")
                    
                    if not isinstance(val, str):
                        parsed_list.append({'Raw_Value': val})
                        continue
                        
                    v = val.strip()
                    # Excel protection: Truncate extremely long texts
                    if len(v) > 30000:
                        v = v[:29900] + "... [Text truncated due to excessive length]"
                        
                    if v in ['error_api', 'error_timeout', 'error_invalid_json', 'error_empty', 'in process']:
                        parsed_list.append({'Raw_Value': v})
                        continue
                        
                    if v.startswith("```"):
                        v = re.sub(r'^```[a-zA-Z]*\n?', '', v)
                        v = re.sub(r'\n?```$', '', v).strip()
                        
                    parsed_result = None
                    try:
                        parsed = json.loads(v)
                        if isinstance(parsed, dict):
                            parsed_result = parsed
                    except json.JSONDecodeError:
                        m = re.search(r'\{.*\}', v, re.DOTALL)
                        if m:
                            try:
                                parsed = json.loads(m.group(0))
                                if isinstance(parsed, dict):
                                    parsed_result = parsed
                            except: pass
                            
                    if parsed_result:
                        expected_keys = task_expected_keys.get(clean_name, [])
                        if expected_keys:
                            # Filter keys (Case-Insensitive Match)
                            filtered_dict = {k: pv for k, pv in parsed_result.items() if str(k).lower() in expected_keys}
                            parsed_list.append(filtered_dict if filtered_dict else {'Raw_Value': v})
                        else:
                            parsed_list.append(parsed_result)
                    else:
                        # Not a JSON (e.g., Classic Classifier like Readability) -> Keep raw text
                        parsed_list.append({'Raw_Value': v})
    
                if len(parsed_list) == len(df):
                    parsed_df = pd.json_normalize(parsed_list)
                    parsed_df.index = df.index
                    parsed_df = parsed_df.add_prefix('Value_')
                    if 'Value' in df.columns:
                        df = df.drop(columns=['Value'])
                    df = pd.concat([df, parsed_df], axis=1)
                    
            except Exception as e:
                pass

        return df

    def get_ai_results_df():
        """
        Collects comprehensive generated raw textual records originating from search engine AI Overviews.
        
        Returns:
            pd.DataFrame: Log containing AI engine text responses mapped across keywords.
        """
        sql_query = text("""
            SELECT 
                ra.id AS ai_result_id, 
                q.query AS keyword, 
                ra.engine_text,
                ra.answer, 
                ra.created_at 
            FROM result_ai ra 
            JOIN query q ON ra.query = q.id 
            WHERE ra.study = :study_id 
            ORDER BY ra.created_at
        """)
        labels = ['AI Result ID', 'Keyword (Query)', 'Search Engine', 'Answer Text', 'Timestamp']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)

    def get_chatbot_results_df():
        """
        Collects system responses generated across full conversation interface Chatbots.
        
        Returns:
            pd.DataFrame: Text log capture for conversational agent outputs.
        """
        sql_query = text("""
            SELECT 
                rc.id AS chatbot_result_id, 
                q.query AS keyword, 
                rc.engine_text,
                rc.answer, 
                rc.created_at 
            FROM result_chatbot rc 
            JOIN query q ON rc.query = q.id 
            WHERE rc.study = :study_id 
            ORDER BY rc.created_at
        """)
        labels = ['Chatbot Result ID', 'Keyword (Query)', 'Search Engine', 'Answer Text', 'Timestamp']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)

    def get_ai_sources_df():
        """
        Extracts specific reference citations or link anchors recommended inside AI responses.
        
        Returns:
            pd.DataFrame: Source list detailing linked titles and source indexes used by generative layers.
        """
        sql_query = text("""
            SELECT 
                ras.result_ai, 
                ras.engine_text, 
                ras.title, 
                ras.description, 
                ras.url, 
                ras.position, 
                ras.main 
            FROM result_ai_source ras 
            WHERE ras.study = :study_id 
            ORDER BY ras.result_ai, ras.position
        """)
        labels = ['AI Result ID', 'Search Engine', 'Title', 'Description', 'URL', 'Position', 'Main']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)

    def get_image_results_df():
        sql_query = text("""
            SELECT 
                ri.id AS image_result_id, 
                q.query AS keyword, 
                ri.engine_text,
                ri.title,
                ri.source_name,
                ri.position,
                ri.source_url,
                ri.image_url,
                ri.created_at 
            FROM result_image ri 
            LEFT JOIN query q ON ri.query = q.id 
            WHERE ri.study = :study_id 
            ORDER BY ri.position
        """)
        labels = ['Image Result ID', 'Keyword (Query)', 'Search Engine', 'Title', 'Source Domain', 'Position', 'Source URL', 'Image URL', 'Timestamp']
        records = db.session.execute(sql_query, {'study_id': id}).all()
        return pd.DataFrame.from_records(records, columns=labels)    
    
    def get_survey_answers_df():
        """
        Parses structured and unstructured JSON survey data answers from pre/post-study forms.
        
        Unpacks flexible JSON blobs saved directly against user profiles into a dense, flat tabular grid, 
        mapping cryptic question tracking keys back into human-readable table headers.
        
        Returns:
            pd.DataFrame: Participant survey matrix where columns represent individualized question entries.
        """
        q_map = {}
        
        # 1. Parse JSON blueprints for Pre-Survey layout structures
        if study.pre_survey_json:
            try:
                pre_qs = json.loads(study.pre_survey_json)
                for q in pre_qs:
                    q_map[q['id']] = f"[PRE] {q['title']}"
            except Exception: pass
            
        # 2. Parse JSON blueprints for Post-Survey layout structures
        if study.post_survey_json:
            try:
                post_qs = json.loads(study.post_survey_json)
                for q in post_qs:
                    q_map[q['id']] = f"[POST] {q['title']}"
            except Exception: pass

        rows = []
        participants = db.session.query(Participant).join(participant_study).filter(participant_study.c.study == id).all()
        
        # Sequentially unpack survey records for each registered cohort member
        for p in participants:
            p_row = {'Participant ID': p.id, 'Participant Name': p.name}
            
            # Process Pre-Survey answers matching the present active study ID scope
            if p.pre_survey_answers:
                try:
                    pre_ans = json.loads(p.pre_survey_answers).get(str(id), {})
                    for q_id, val in pre_ans.items():
                        col_name = q_map.get(q_id, q_id)
                        # Cleanly convert checkbox choice list arrays into explicit standard strings
                        if isinstance(val, list): val = ", ".join(val)
                        p_row[col_name] = val
                except Exception: pass
                
            # Process Post-Survey answers matching the present active study ID scope
            if p.post_survey_answers:
                try:
                    post_ans = json.loads(p.post_survey_answers).get(str(id), {})
                    for q_id, val in post_ans.items():
                        col_name = q_map.get(q_id, q_id)
                        if isinstance(val, list): val = ", ".join(val)
                        p_row[col_name] = val
                except Exception: pass
                
            rows.append(p_row)
            
        return pd.DataFrame(rows)

    def format_domain_df(domain_data, data_key):
        """
        Standardizes format presentation variables inside computed domain distribution lists.
        
        Args:
            domain_data (dict): Nested dictionary summary generated by analytical helper functions.
            data_key (str): Targeting identifier ('standard_results' or 'ai_sources').
            
        Returns:
            pd.DataFrame: Clean sorted representation data displaying formatted percentage shares.
        """
        if not domain_data or data_key not in domain_data: return pd.DataFrame()
        df = pd.DataFrame(domain_data[data_key])
        if df.empty: return pd.DataFrame()
        
        # Humanize structural display types for easy presentation reading
        df['percentage'] = df['percentage'].apply(lambda x: f"{x:.2f}%")
        if 'avg_position' in df.columns:
            df['avg_position'] = df['avg_position'].apply(lambda x: f"{x:.2f}" if x is not None else 'N/A')
        df.rename(columns={'percentage': 'Share of Total', 'avg_position': 'Avg. Position'}, inplace=True)
        return df

    def get_top_domains_standard_df():
        """
        Fetches distribution frequency metrics covering standard organic visibility shares.
        
        Returns:
            pd.DataFrame: Normalized presentation showing top visible domains.
        """
        data = get_top_main_domains(study, limit=None)
        return format_domain_df(data, 'standard_results') if data else pd.DataFrame()

    def get_top_domains_ai_df():
        """
        Fetches visibility distribution data covering websites linked inside generative answers.
        
        Returns:
            pd.DataFrame: Normalized metrics showing top visible domains cited within AI contexts.
        """
        data = get_top_main_domains(study, limit=None)
        return format_domain_df(data, 'ai_sources') if data else pd.DataFrame()

    # Establish localized validation state checks to isolate which sheets can be safely built
    top_domains_preview = get_top_main_domains(study, limit=1)
    
    has_survey_data = bool((study.pre_survey_json and study.pre_survey_json.strip() not in ['', '[]']) or 
                           (study.post_survey_json and study.post_survey_json.strip() not in ['', '[]']))
    
    # Check classifier data across all source types
    def check_classifier_exists(model_class):
        q = db.session.query(model_class.id).filter(
            db.or_(
                model_class.study_id == id,
                model_class.result_id.in_(db.session.query(Result.id).filter(Result.study_id == id)),
                model_class.result_ai_id.in_(db.session.query(ResultAi.id).filter(ResultAi.study_id == id)),
                model_class.result_chatbot_id.in_(db.session.query(ResultChatbot.id).filter(ResultChatbot.study_id == id)),
                model_class.result_ai_source_id.in_(db.session.query(ResultAiSource.id).filter(ResultAiSource.study_id == id))
            )
        )
        return q.first() is not None
        
    # Check data availability flags before initializing runtime generator steps
    available_data = {
        'study_metadata': True,
        'assessments': db.session.query(Answer).filter(Answer.study_id == id).first() is not None,
        'survey_answers': has_survey_data,
        'questions': db.session.query(Question).filter(Question.study_id == id).first() is not None,
        'search_results': db.session.query(Result).filter(Result.study_id == id).first() is not None,
        'serp_results_master': db.session.query(Serp).filter(Serp.study_id == id).first() is not None, 
        'classifier_results': check_classifier_exists(ClassifierResult),
        'classifier_indicators': check_classifier_exists(ClassifierIndicator),
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
        'image_results': db.session.query(ResultImage).filter(ResultImage.study_id == id).first() is not None,
    }
    
    # Process requests requesting direct generation payload file responses
    if request.method == 'POST':
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Registry configuration matrix tying user choices to distinct data operations
        export_options = {
            'study_metadata': ("Study Overview", get_study_metadata_df),
            'result_stats': ("Result Stats", lambda: pd.DataFrame(list(result_stats_data.items()), columns=['Statistic', 'Value'])),
            'evaluation_stats': ("Evaluation Stats", lambda: pd.DataFrame([s for s in evaluation_stats_data.items() if s[0] != 'breakdown'], columns=['Statistic', 'Value'])),
            'evaluation_breakdown': ("Evaluation Breakdown", lambda: pd.DataFrame(evaluation_stats_data['breakdown']) if evaluation_stats_data and 'breakdown' in evaluation_stats_data else pd.DataFrame()),
            'answer_stats': ("Answer Stats", lambda: convert_answer_stats_to_df(answer_stats_data)),
            'classifier_stats': ("Classifier Stats", lambda: pd.DataFrame([{'Classifier': cls, 'Value': val, 'Count': data['count'], 'Percentage of Total': f"{data['percentage']:.2f}%"} for cls, values in classifier_stats_data.items() for val, data in values.get('raw_stats', {}).items()]) if classifier_stats_data else pd.DataFrame()),
            'top_domains_standard': ("All Domains (Standard)", get_top_domains_standard_df),
            'top_domains_ai': ("All Domains (AI Sources)", get_top_domains_ai_df),
            'assessments': ("Assessments", get_assessments_df),
            'survey_answers': ("Participant Surveys", get_survey_answers_df),
            'search_results': ("Search Results", get_search_results_df),
            'serp_results_master': ("SERP Results Master", get_serp_results_master_df), 
            'ai_results': ("AI Overview Results", get_ai_results_df),
            'chatbot_results': ("Chatbot Results", get_chatbot_results_df),
            'ai_sources': ("AI Overview Sources", get_ai_sources_df),
            'classifier_results': ("Classifier Results", get_classifier_results_df),
            'classifier_indicators': ("Classifier Indicators", get_classifier_indicators_df),
            'questions': ("Questions", lambda: pd.read_sql_query(db.session.query(Question).filter(Question.study_id == id).statement, engine))
        }
        
        # Iterate over verified option choices to compile targeted data sections
        for key, (label, func) in export_options.items():
            if available_data.get(key, False):
                df = func()
                if not df.empty:
                    df.to_excel(writer, sheet_name=label, index=False)
        
        # Save modifications and reset pointer before delivering file streaming array
        writer.close()
        output.seek(0)

        # Sanitize internal study name values into secure file string formats
        safe_study_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', study.name)
        
        filename = f"study_{id}_{safe_study_name}_full_report_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        
        return send_file(output, download_name=filename, as_attachment=True)

    return render_template('exports/assessment_export.html',
                           form=form,
                           id=id,
                           available_data=available_data)