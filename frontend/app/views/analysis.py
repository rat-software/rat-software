from .. import app, db
from ..models import Study, Result
from flask import render_template, send_file, redirect, url_for
from flask_security import login_required
from .analysis_func import (get_result_stats, get_evaluation_stats,
                           get_classifier_stats, get_top_main_domains, 
                           get_answer_stats, convert_answer_stats_to_df,
                           get_overlap_stats)

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
    
    # HIER WAR DER FEHLER: studytype.id entfernt. Wir laden die Stats jetzt einfach immer.
    evaluation_stats = get_evaluation_stats(study) 
    
    top_domains = get_top_main_domains(study)
    answer_stats = get_answer_stats(study)
    overlap_list = get_overlap_stats(study)
    
    # Standard: Wir laden für das Dashboard die gefilterten Classifier-Daten (passend zum Limit)
    raw_classifier_stats = get_classifier_stats(study, use_limit=True)
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
    Veraltete Route: Leitet jetzt auf den zentralen Export um.
    """
    return redirect(url_for('export', id=id))