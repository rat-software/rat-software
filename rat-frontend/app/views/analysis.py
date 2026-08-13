"""
Analysis module for the RAT application.

This file contains the routing and data processing logic required to generate 
and render the analysis dashboard for a specific study. It processes statistics 
from results, evaluations, classifiers, and domains to be passed to the view layer.
"""

from .. import app, db
from ..models import Study
from flask import render_template, redirect, url_for
from flask_security import login_required
from .analysis_func import (get_result_stats, get_evaluation_stats,
                           get_classifier_stats, get_top_main_domains, 
                           get_answer_stats, convert_answer_stats_to_df,
                           get_overlap_stats, get_query_evaluation_stats)

import pandas as pd
import io
import re
from ..models import Study, ClassifierIndicator, ClassifierResult

def slugify(s):
    """
    Converts a string into a URL-friendly slug.

    This function converts the input string to lowercase, removes any non-word
    characters (keeping spaces and hyphens), replaces spaces and underscores 
    with hyphens, and strips leading/trailing hyphens.

    Example: "Machine Learning!" -> "machine-learning"

    Args:
        s (str): The original string to convert.

    Returns:
        str: The sanitized, URL-friendly slug.
    """
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s

app.jinja_env.filters['slugify'] = slugify

def _get_analysis_data(study_id):
    """
    Collects and processes all data required for the analysis dashboard page.

    This helper function aggregates general statistics, evaluation results, 
    classifier performance, and domain overlap metrics for a given study. 
    It also groups numeric classifier scores into fixed buckets for visualization.

    Args:
        study_id (int): The unique identifier of the study.

    Returns:
        dict: A comprehensive dictionary containing all aggregated statistics 
              and study metadata required by the Jinja template.
    """
    # Fetch the study or return a 404 error if it doesn't exist
    study = Study.query.get_or_404(study_id)
    
    # Gather general statistics for the dashboard
    result_stats = get_result_stats(study)
    
    # We always load evaluation stats now, regardless of the study type
    evaluation_stats = get_evaluation_stats(study) 
    
    # Fetch additional data for the charts and tables
    top_domains = get_top_main_domains(study, limit=250)
    
    answer_stats = get_answer_stats(study)
    overlap_list = get_overlap_stats(study)
    
    query_eval_stats = get_query_evaluation_stats(study)
    
    # Standard approach: We load the filtered classifier data for the dashboard 
    raw_classifier_stats = get_classifier_stats(study, use_limit=True)
    processed_classifier_stats = {}

    def process_stats_dict(stats_dict):
        # 1. Define explicit system errors (no word fragments)
        system_errors = ['error', 'source_failed', 'classifier_error', 'excluded', 
                         'error_api', 'error_timeout', 'error_empty', 'error_no_config', 'error_no_study']
        
        others = {}
        total_count = sum(stats_dict.values())
        
        # 2. Analyze numeric values to decide if bucketing (0-100) makes sense
        numeric_values = []
        for value in stats_dict.keys():
            try:
                val_str = str(value).split(':')[-1].strip()
                numeric_values.append(float(val_str))
            except ValueError:
                pass
                
        needs_bucketing = False
        if numeric_values:
            max_val = max(numeric_values)
            unique_vals = len(set(numeric_values))

            if max_val > 10 and unique_vals > 10:
                needs_bucketing = True

        groups = {
            '0-20': {'count': 0}, '21-40': {'count': 0}, '41-60': {'count': 0},
            '61-80': {'count': 0}, '81-100': {'count': 0},
        }
        
        for value, count in stats_dict.items():
            val_str = str(value).strip()
            val_lower = val_str.lower()
            
            if val_lower in system_errors or val_lower.startswith('error_'):
                display_val = 'Error'
                if display_val not in others: others[display_val] = {'count': 0}
                others[display_val]['count'] += count
                continue
                
            if val_lower == 'in process':
                display_val = 'In Process'
                if display_val not in others: others[display_val] = {'count': 0}
                others[display_val]['count'] += count
                continue
                
            is_numeric = False
            try:
                num_val = float(val_str.split(':')[-1].strip())
                is_numeric = True
            except ValueError:
                pass
                
            # Assign to buckets using floating-point inclusive logic
            if is_numeric and needs_bucketing:
                if 0 <= num_val <= 20: groups['0-20']['count'] += count
                elif 20 < num_val <= 40: groups['21-40']['count'] += count
                elif 40 < num_val <= 60: groups['41-60']['count'] += count
                elif 60 < num_val <= 80: groups['61-80']['count'] += count
                elif 80 < num_val <= 100: groups['81-100']['count'] += count
                else: 
                    display_val = str(value)
                    if display_val not in others: others[display_val] = {'count': 0}
                    others[display_val]['count'] += count
            else:
                display_val = val_str
                if display_val not in others: others[display_val] = {'count': 0}
                others[display_val]['count'] += count
                
        if needs_bucketing:
            grouped_stats = {**groups, **others}
        else:
            grouped_stats = others
            
        for key, data_dict in grouped_stats.items():
            data_dict['percentage'] = (data_dict['count'] / total_count) * 100 if total_count > 0 else 0
            
        grouped_stats = {k: v for k, v in grouped_stats.items() if v['count'] > 0}
        grouped_stats = dict(sorted(grouped_stats.items(), key=lambda item: item[1]['count'], reverse=True))

        # LIMIT DOM RENDERING to prevent browser freezes with thousands of distinct text values
        MAX_ROWS = 15
        if len(grouped_stats) > MAX_ROWS:
            top_stats = {}
            other_count = 0
            for i, (k, v) in enumerate(grouped_stats.items()):
                if i < MAX_ROWS:
                    top_stats[k] = v
                else:
                    other_count += v['count']
            
            if other_count > 0:
                top_stats['... (Other distinct values)'] = {
                    'count': other_count,
                    'percentage': (other_count / total_count) * 100 if total_count > 0 else 0
                }
            grouped_stats = top_stats

        numeric_raw_stats = []
        total_numeric_count = 0
        for value, count in stats_dict.items():
            try:
                val_lower = str(value).strip().lower()
                if val_lower in system_errors or val_lower.startswith('error_') or val_lower == 'in process':
                    continue
                numeric_value = float(str(value).split(':')[-1].strip())
                numeric_raw_stats.append({
                    "value": numeric_value,
                    "count": count,
                    "percentage": (count / total_count) * 100 if total_count > 0 else 0
                })
                total_numeric_count += count
            except (ValueError, IndexError):
                continue
        numeric_raw_stats.sort(key=lambda x: x['value'])

        return {
            'grouped_stats': grouped_stats,
            'numeric_raw_stats': numeric_raw_stats,
            'total_numeric_count': total_numeric_count,
            'needs_bucketing': needs_bucketing
        }
    if raw_classifier_stats:
        for classifier_name, clf_data in raw_classifier_stats.items():
            processed_classifier_stats[classifier_name] = {
                'is_json': clf_data.get('is_json', False),
                'source_types': {}
            }
            
            if clf_data.get('is_json'):
                all_keys = set()
                for st, st_data in clf_data.get('source_types', {}).items():
                    if 'keys' in st_data:
                        all_keys.update(st_data['keys'].keys())
                processed_classifier_stats[classifier_name]['available_keys'] = sorted(list(all_keys))

            for source_type, st_data in clf_data.get('source_types', {}).items():
                processed_st = {}
                if clf_data.get('is_json'):
                    processed_st['json_keys'] = {}
                    if 'keys' in st_data:
                        for k, k_stats in st_data['keys'].items():
                            combined = dict(k_stats)
                            if 'raw_stats' in st_data:
                                for err_k, err_v in st_data['raw_stats'].items():
                                    combined[err_k] = combined.get(err_k, 0) + err_v
                            processed_st['json_keys'][k] = process_stats_dict(combined)
                else:
                    processed_st['classic'] = process_stats_dict(st_data.get('raw_stats', {}))
                    
                processed_classifier_stats[classifier_name]['source_types'][source_type] = processed_st

    error_vals = ['error_api', 'error_timeout', 'error_empty', 'error_invalid_json', 'error_no_config', 'error_no_study']
    
    has_classifier_errors = db.session.query(ClassifierIndicator.id).filter(
        ClassifierIndicator.study_id == study.id,
        ClassifierIndicator.value.in_(error_vals)
    ).first() is not None
    
    if not has_classifier_errors:
        has_classifier_errors = db.session.query(ClassifierResult.id).filter(
            ClassifierResult.study_id == study.id,
            ClassifierResult.value.in_(error_vals + ['error', 'classifier_error', 'source_failed'])
        ).first() is not None

    return {
        'study': study, 
        'result_stats': result_stats, 
        'evaluation_stats': evaluation_stats,
        'classifier_stats': processed_classifier_stats, 
        'top_domains': top_domains, 
        'overlap_list': overlap_list, 
        'answer_stats': answer_stats,
        'query_eval_stats': query_eval_stats,
        'has_classifier_errors': has_classifier_errors # <-- Die neue Variable für das HTML
    }


@app.route('/<int:id>/analysis')
@login_required
def analysis(id):
    """
    Renders the main analysis dashboard for a specific study.

    Args:
        id (int): The unique identifier of the study.

    Returns:
        str: The rendered HTML template for the analysis dashboard.
    """
    analysis_data = _get_analysis_data(id)
    return render_template('analysis/analysis.html', **analysis_data)


@app.route('/<int:id>/export-analysis')
@login_required
def export_analysis(id):
    """
    Deprecated route: Safely redirects to the central export handler.

    Args:
        id (int): The unique identifier of the study to be exported.

    Returns:
        Response: A Flask redirect response to the new central export route.
    """
    return redirect(url_for('export', id=id))

@app.route('/<int:id>/retry_classifier_errors', methods=['POST'])
@login_required
def retry_classifier_errors(id):
    """
    Clears out all explicit error states for classifiers and LLM tasks.
    This effectively resets the queue, allowing the background worker to pick them up again.
    """
    error_vals = ['error_api', 'error_timeout', 'error_empty', 'error_invalid_json', 'error_no_config', 'error_no_study']
    
    db.session.query(ClassifierIndicator).filter(
        ClassifierIndicator.study_id == id,
        ClassifierIndicator.value.in_(error_vals)
    ).delete(synchronize_session=False)
    
    db.session.query(ClassifierResult).filter(
        ClassifierResult.study_id == id,
        ClassifierResult.value.in_(error_vals + ['error', 'classifier_error', 'source_failed'])
    ).delete(synchronize_session=False)
    
    db.session.commit()
    from flask import flash
    flash('Failed AI & Classifier tasks have been reset and queued for a new background retry.', 'success')
    
    return redirect(url_for('analysis', id=id))