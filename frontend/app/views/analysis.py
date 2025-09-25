from .. import app, db
from ..models import Study, Result, Scraper
from flask import render_template, send_file
from flask_security import login_required
from itertools import combinations
from .analysis_func import (get_result_stats, get_evaluation_stats,
                           get_classifier_stats, get_top_main_domains, get_answer_stats, convert_answer_stats_to_df)

import pandas as pd
import io
import re

def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s

app.jinja_env.filters['slugify'] = slugify

def _get_analysis_data(study_id):
    """
    Eine zentrale Helferfunktion, die alle Daten für die Analyse-Seite sammelt und aufbereitet.
    """
    study = Study.query.get_or_404(study_id)
    result_stats = get_result_stats(study)
    evaluation_stats = get_evaluation_stats(study) if study.studytype.id == 1 else None
    top_domains = get_top_main_domains(study)
    answer_stats = get_answer_stats(study)
    
    raw_classifier_stats = get_classifier_stats(study)
    processed_classifier_stats = {}

    if raw_classifier_stats:
        for name, stats in raw_classifier_stats.items():
            groups = {
                '0-20': {'count': 0}, '21-40': {'count': 0}, '41-60': {'count': 0},
                '61-80': {'count': 0}, '81-100': {'count': 0},
            }
            others = {}
            total_count = sum(data.get('count', 0) for data in stats.values())
            for value, data in stats.items():
                count = data.get('count', 0)
                try:
                    numeric_value = float(str(value).split(':')[-1].strip())
                    if 0 <= numeric_value <= 20: groups['0-20']['count'] += count
                    elif 21 <= numeric_value <= 40: groups['21-40']['count'] += count
                    elif 41 <= numeric_value <= 60: groups['41-60']['count'] += count
                    elif 61 <= numeric_value <= 80: groups['61-80']['count'] += count
                    elif 81 <= numeric_value <= 100: groups['81-100']['count'] += count
                except (ValueError, IndexError):
                    if value not in others: others[value] = {'count': 0}
                    others[value]['count'] += count
            
            grouped_stats = {**groups, **others}
            for key, data_dict in grouped_stats.items():
                data_dict['percentage'] = (data_dict['count'] / total_count) * 100 if total_count > 0 else 0

            numeric_raw_stats = []
            total_numeric_count = 0
            for value, data in stats.items():
                try:
                    numeric_value = float(str(value).split(':')[-1].strip())
                    count = data.get('count', 0)
                    numeric_raw_stats.append({
                        "value": numeric_value,
                        "count": count,
                        "percentage": data.get('percentage', 0)
                    })
                    total_numeric_count += count
                except (ValueError, IndexError):
                    continue
            
            numeric_raw_stats.sort(key=lambda x: x['value'])

            processed_classifier_stats[name] = {
                'raw_stats': stats, 
                'grouped_stats': grouped_stats,
                'numeric_raw_stats': numeric_raw_stats,
                'total_numeric_count': total_numeric_count
            }

    overlap_list = None
    if len(study.searchengines) > 1:
        se_list = {}
        for se in study.searchengines:
            q = db.session.query(Result.normalized_url).join(Scraper).filter(
                Result.study == study,
                Scraper.searchengine_id == se.id,
                Scraper.resulttype == 1
            )
            urls = {r.normalized_url for r in q.all()}
            
            if urls:
                se_list[se.name] = {"Sources": urls}
        
        if len(se_list) > 1:
            overlap_list = []
            for (name1, data1), (name2, data2) in combinations(se_list.items(), 2):
                k = f"{name1}-{name2}"
                only_1 = len(data1["Sources"] - data2["Sources"])
                only_2 = len(data2["Sources"] - data1["Sources"])
                overlap_val = len(data1["Sources"].intersection(data2["Sources"]))
                total = len(data1["Sources"].union(data2["Sources"]))
                overlap = {"SE_Pair": k, "SE_1": name1, "SE_1 exclusive": only_1,
                           "SE_2": name2, "SE_2 exclusive": only_2, "Overlap": overlap_val, "Total": total}
                overlap_list.append(overlap)

    return {
        'study': study, 'result_stats': result_stats, 'evaluation_stats': evaluation_stats,
        'classifier_stats': processed_classifier_stats, 'top_domains': top_domains, 
        'overlap_list': overlap_list, 'answer_stats': answer_stats
    }

@app.route('/<int:id>/analysis')
@login_required
def analysis(id):
    analysis_data = _get_analysis_data(id)
    return render_template('analysis/analysis.html', **analysis_data)


@app.route('/<int:id>/export-analysis')
@login_required
def export_analysis(id):
    """
    Erstellt eine XLSX-Datei mit allen Statistik-Tabellen (ohne Diagramme).
    Für Domains werden ALLE exportiert, nicht nur die Top 10.
    """
    data = _get_analysis_data(id)
    study = data['study'] # Studie aus den Daten holen
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        if data['result_stats']:
            df_results = pd.DataFrame(list(data['result_stats'].items()), columns=['Statistic', 'Value'])
            df_results.to_excel(writer, sheet_name='General Statistics', index=False)

        if data['evaluation_stats']:
            # ... (dieser Block bleibt unverändert) ...
            sheet_name = 'Evaluation Statistics'
            main_stats = {k: v for k, v in data['evaluation_stats'].items() if k != 'breakdown'}
            df_eval_main = pd.DataFrame(list(main_stats.items()), columns=['Statistic', 'Value'])
            df_eval_main.to_excel(writer, sheet_name=sheet_name, index=False)
            if data['evaluation_stats'].get('breakdown'):
                df_eval_breakdown = pd.DataFrame(data['evaluation_stats']['breakdown'])
                start_row = len(df_eval_main) + 2
                df_eval_breakdown.to_excel(writer, sheet_name=sheet_name, index=False, startrow=start_row)

        if data['answer_stats']:
            df_answer_stats = convert_answer_stats_to_df(data['answer_stats'])
            if not df_answer_stats.empty:
                df_answer_stats.to_excel(writer, sheet_name='Answer Stats', index=False)
        
        # HINZUGEFÜGT: Rufe ALLE Domains für den Export ab
        all_domains_data = get_top_main_domains(study, limit=None)

        if all_domains_data and all_domains_data.get('standard_results'):
            df_top_std = pd.DataFrame(all_domains_data['standard_results'])
            df_top_std.to_excel(writer, sheet_name='All Domains (Standard)', index=False)
        
        if all_domains_data and all_domains_data.get('ai_sources'):
            df_top_ai = pd.DataFrame(all_domains_data['ai_sources'])
            df_top_ai.to_excel(writer, sheet_name='All Domains (AI Sources)', index=False)

        if data['classifier_stats']:
            # ... (dieser Block bleibt unverändert) ...
            sheet_name = 'Classifier Statistics'
            all_raw_stats = []
            for name, data_bundle in data['classifier_stats'].items():
                for item in data_bundle['numeric_raw_stats']:
                    all_raw_stats.append({
                        'Classifier': name, 'Value': item['value'], 'Count': item['count'], 
                        'Share (%)': item['percentage']
                    })
            if all_raw_stats:
                df_raw = pd.DataFrame(all_raw_stats)
                df_raw.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
        
        if data['overlap_list']:
            df_overlap = pd.DataFrame(data['overlap_list'])
            df_overlap.to_excel(writer, sheet_name='Overlap Analysis', index=False)

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f"study_{id}_analysis_export.xlsx"
    )