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

def slugify(s):
    """
    Converts a string into a URL-friendly slug.
    Example: "Machine Learning!" -> "machine-learning"
    """
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s

# Register the slugify function as a Jinja2 filter so it can be used in HTML templates
app.jinja_env.filters['slugify'] = slugify

def _get_analysis_data(study_id):
    """
    A central helper function that collects and processes all data required 
    for the analysis dashboard page.
    """
    # Fetch the study or return a 404 error if it doesn't exist
    study = Study.query.get_or_404(study_id)
    
    # Gather general statistics for the dashboard
    result_stats = get_result_stats(study)
    
    # We always load evaluation stats now, regardless of the study type
    evaluation_stats = get_evaluation_stats(study) 
    
    # Fetch additional data for the charts and tables
    top_domains = get_top_main_domains(study)
    answer_stats = get_answer_stats(study)
    overlap_list = get_overlap_stats(study)
    
    query_eval_stats = get_query_evaluation_stats(study)
    
    # Standard approach: We load the filtered classifier data for the dashboard 
    # (matching the result limit defined in the study, if any)
    raw_classifier_stats = get_classifier_stats(study, use_limit=True)
    processed_classifier_stats = {}

    if raw_classifier_stats:
        for name, stats in raw_classifier_stats.items():
            # Initialize predefined buckets for numeric scores (0-100)
            groups = {
                '0-20': {'count': 0}, '21-40': {'count': 0}, '41-60': {'count': 0},
                '61-80': {'count': 0}, '81-100': {'count': 0},
            }
            others = {}
            total_count = sum(data.get('count', 0) for data in stats.values())
            
            for value, data in stats.items():
                count = data.get('count', 0)
                try:
                    # Attempt to extract and parse a numeric score if it's formatted with a colon
                    # (e.g., "Score: 85") or if it's just a raw number ("85").
                    numeric_value = float(str(value).split(':')[-1].strip())
                    
                    # Sort the numeric values into their respective percentage buckets
                    if 0 <= numeric_value <= 20: groups['0-20']['count'] += count
                    elif 21 <= numeric_value <= 40: groups['21-40']['count'] += count
                    elif 41 <= numeric_value <= 60: groups['41-60']['count'] += count
                    elif 61 <= numeric_value <= 80: groups['61-80']['count'] += count
                    elif 81 <= numeric_value <= 100: groups['81-100']['count'] += count
                except (ValueError, IndexError):
                    # If conversion to float fails, it's a string status (e.g., an error or progress flag)
                    
                    # Normalize and bundle the error states for a cleaner dashboard UI
                    val_str = str(value).strip().lower()
                    
                    # EXACT MATCHES: Check for known exact error flags
                    if val_str in ['error', 'source_failed', 'classifier_error', 'excluded']:
                        display_val = 'Error'
                        
                    # PARTIAL MATCHES: Catch verbose errors from libraries (e.g., "Language 'bn' not supported")
                    elif 'not supported' in val_str or 'error' in val_str or 'failed' in val_str:
                        display_val = 'Error'
                        
                    # PROGRESS MATCHES
                    elif val_str == 'in process':
                        display_val = 'In Process'
                        
                    # FALLBACK
                    else:
                        display_val = value # Fallback for any other unexpected strings
                        
                    # Add to the 'others' dictionary under the normalized display name
                    if display_val not in others: others[display_val] = {'count': 0}
                    others[display_val]['count'] += count
            
            # Combine the numeric buckets and the text-based statuses
            grouped_stats = {**groups, **others}
            
            # Calculate percentages for the UI
            for key, data_dict in grouped_stats.items():
                data_dict['percentage'] = (data_dict['count'] / total_count) * 100 if total_count > 0 else 0

            # Prepare raw numeric data for more detailed charts (e.g., line charts or histograms)
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
            
            # Sort the raw numeric stats by value in ascending order
            numeric_raw_stats.sort(key=lambda x: x['value'])

            # Store the fully processed bundle for this specific classifier
            processed_classifier_stats[name] = {
                'raw_stats': stats, 
                'grouped_stats': grouped_stats,
                'numeric_raw_stats': numeric_raw_stats,
                'total_numeric_count': total_numeric_count
            }

    return {
        'study': study, 
        'result_stats': result_stats, 
        'evaluation_stats': evaluation_stats,
        'classifier_stats': processed_classifier_stats, 
        'top_domains': top_domains, 
        'overlap_list': overlap_list, 
        'answer_stats': answer_stats,
        'query_eval_stats': query_eval_stats
    }

@app.route('/<int:id>/analysis')
@login_required
def analysis(id):
    """
    Renders the main analysis dashboard for a specific study.
    """
    analysis_data = _get_analysis_data(id)
    return render_template('analysis/analysis.html', **analysis_data)


@app.route('/<int:id>/export-analysis')
@login_required
def export_analysis(id):
    """
    Deprecated route: Now safely redirects to the central export handler.
    """
    return redirect(url_for('export', id=id))