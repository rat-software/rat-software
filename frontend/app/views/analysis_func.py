from .. import app, db
from ..models import (Study, Scraper, Answer, Result, ResultAi, ResultSource, 
                      Classifier, ClassifierResult, ResultAiSource, ResultType, ResultChatbot,
                      Source, Evaluation)
from sqlalchemy import func, or_, and_
from ..helpers import percentage_calc
import pandas as pd
from itertools import combinations

def get_result_stats(study):
    scrapers_all = db.session.query(Scraper.id).filter(Scraper.study_id == study.id).count()
    scrapers_done = db.session.query(Scraper.id).filter(
        Scraper.study_id == study.id,
        or_(Scraper.progress == 1, and_(Scraper.progress == -1, Scraper.counter > 10))
    ).count()
    scraper_percent = (scrapers_done / scrapers_all) * 100 if scrapers_all > 0 else 0

    total_results_to_process = db.session.query(Result.id).filter(Result.study_id == study.id).count()
    
    # --- NEU: Live Mode Logik ---
    if study.live_link_mode:
        collection_status_display = "N/A (Live Mode)"
    else:
        collection_status_percent = scraper_percent
        if total_results_to_process > 0 or scrapers_all > 0:
            finished_sources = db.session.query(ResultSource.result_id).join(Result).filter(
                Result.study_id == study.id,
                or_(ResultSource.progress == 1, and_(ResultSource.progress == -1, ResultSource.counter > 2))
            ).count()

            total_tasks = scrapers_all + total_results_to_process
            finished_tasks = scrapers_done + finished_sources
            
            if total_tasks > 0:
                collection_status_percent = (finished_tasks / total_tasks) * 100
            elif scrapers_done == scrapers_all and scrapers_all > 0:
                collection_status_percent = 100
            else:
                collection_status_percent = 0
                
        collection_status_display = f"{round(collection_status_percent)}%"

    result_stats = {
        "Queries": len(study.queries),
        "Search Engines": len(study.searchengines),
        "Results to Collect per Query": study.result_count,
        "Collection Status": collection_status_display
    }

    if total_results_to_process > 0:
        result_stats["Total Standard Results Found"] = total_results_to_process

        # --- NEU: Download-Stats nur anzeigen, wenn NICHT im Live Mode ---
        if not study.live_link_mode:
            processed_results_count = db.session.query(Result.id)\
                .join(Result.source_associations)\
                .filter(Result.study_id == study.id, ResultSource.progress == 1)\
                .distinct().count()
            
            failed_results_count = db.session.query(Result.id)\
                .join(Result.source_associations)\
                .filter(Result.study_id == study.id, ResultSource.progress == -1)\
                .distinct().count()
            
            if processed_results_count > 0 or failed_results_count > 0:
                result_stats["Results with Processed Source"] = processed_results_count
                result_stats["Results with Failed Source"] = failed_results_count

    ai_results_count = db.session.query(ResultAi).filter(ResultAi.study_id == study.id).count()
    if ai_results_count > 0:
        result_stats["AI Overviews Collected"] = ai_results_count

    chatbot_results_count = db.session.query(ResultChatbot).filter(ResultChatbot.study_id == study.id).count()
    if chatbot_results_count > 0:
        result_stats["Chatbot Results Collected"] = chatbot_results_count
        
    return result_stats

def get_evaluation_stats(study):
    num_questions = len(study.questions)
    if num_questions == 0:
        return {
            "Participants": len(study.participants),
            "Questions": 0,
            "Evaluation Status": "0%",
            "Evaluations Skipped": 0
        }

    evals = db.session.query(Answer).filter(Answer.study == study)
    
    if study.participants:
        evals = evals.filter(Answer.participant_id.isnot(None))
    
    evals_done_answers = evals.filter(Answer.status == 1).count()
    evals_skipped_answers = evals.filter(Answer.status == 2).count()
    evals_all_answers = evals.count()
    
    evals_finished_answers = evals_done_answers + evals_skipped_answers
    evals_stat = percentage_calc(evals_finished_answers, evals_all_answers, "str")

    skipped_items = evals_skipped_answers // num_questions if num_questions > 0 else 0

    evaluation_stats = {
        "Participants": len(study.participants),
        "Questions": num_questions,
        "Evaluation Status": evals_stat,
        "Evaluations Skipped": skipped_items
    }
    
    breakdown_query_obj = db.session.query(
        ResultType.display,
        func.count(Answer.id)
    ).select_from(Answer).join( 
        ResultType, Answer.resulttype == ResultType.id
    ).filter(
        Answer.study_id == study.id,
        Answer.status == 1
    )

    if study.participants:
        breakdown_query_obj = breakdown_query_obj.filter(Answer.participant_id.isnot(None))
    

    breakdown_query = breakdown_query_obj.group_by(
        ResultType.display
    ).order_by(
        ResultType.display
    ).all()
    
    if breakdown_query:
        breakdown_list = []
        for display_name, answer_count in breakdown_query:
            item_count = answer_count // num_questions
            breakdown_list.append({"type": display_name, "count": item_count})

        if breakdown_list:
            evaluation_stats['breakdown'] = breakdown_list

    return evaluation_stats


def get_classifier_stats(study, use_limit=True):
    # --- NEU: Bricht sofort ab, wenn Live Mode an ist ---
    if not study.classifier or study.live_link_mode:
        return None

    total_query = db.session.query(Result.id).filter(Result.study_id == study.id)
    
    if use_limit and study.result_count:
        total_query = total_query.filter(Result.position <= int(study.result_count))
    
    total_results_in_study = total_query.count()

    all_classifier_stats = {}

    for classifier in study.classifier:
        stats_query = db.session.query(
            ClassifierResult.value,
            func.count(ClassifierResult.id)
        ).join(
            Result, ClassifierResult.result_id == Result.id
        ).filter(
            Result.study_id == study.id,
            ClassifierResult.classifier_id == classifier.id
        )
        
        if use_limit and study.result_count:
            stats_query = stats_query.filter(Result.position <= int(study.result_count))

        value_counts = stats_query.group_by(
            ClassifierResult.value
        ).order_by(
            func.count(ClassifierResult.id).desc()
        ).all()

        if value_counts:
            stats_dict = {}
            for value, count in value_counts:
                stats_dict[value] = {
                    "count": count,
                    "percentage": (count / total_results_in_study) * 100 if total_results_in_study > 0 else 0
                }
            all_classifier_stats[classifier.display_name] = stats_dict
            
    return all_classifier_stats if all_classifier_stats else None


def get_top_main_domains(study, limit=10):
    top_domains_data = {}

    # --- 1. Organic Standard Results (Alle hochgeladenen) ---
    total_q = db.session.query(Result.id).filter(
        Result.study_id == study.id, Result.main.isnot(None)
    )
    total_count = total_q.count()

    if total_count > 0:
        query = db.session.query(
            Result.main,
            func.count(Result.id).label('count'),
            func.avg(Result.position).label('avg_pos')
        ).filter(
            Result.study_id == study.id,
            Result.main.isnot(None)
        ).group_by(Result.main).order_by(func.count(Result.id).desc())

        if limit:
            query = query.limit(limit)

        results = query.all()
        top_domains_data['standard_results'] = [
            {
                "domain": domain,
                "count": count,
                "percentage": (count / total_count) * 100,
                "avg_position": avg_pos
            } for domain, count, avg_pos in results
        ]

    # --- 2. AI Sources (Bleibt unverändert) ---
    total_ai_sources_with_main = db.session.query(ResultAiSource.id).filter(
        ResultAiSource.study_id == study.id, ResultAiSource.main.isnot(None)
    ).count()

    if total_ai_sources_with_main > 0:
        query = db.session.query(
            ResultAiSource.main,
            func.count(ResultAiSource.id).label('count'),
            func.avg(ResultAiSource.position).label('avg_pos')
        ).filter(
            ResultAiSource.study_id == study.id,
            ResultAiSource.main.isnot(None)
        ).group_by(ResultAiSource.main).order_by(func.count(ResultAiSource.id).desc())
        
        if limit:
            query = query.limit(limit)

        top_ai_sources = query.all()

        top_domains_data['ai_sources'] = [
            {
                "domain": domain,
                "count": count,
                "percentage": (count / total_ai_sources_with_main) * 100,
                "avg_position": avg_pos
            } for domain, count, avg_pos in top_ai_sources
        ]

    return top_domains_data if top_domains_data else None

def get_answer_stats(study):
    if not study.questions:
        return None

    all_question_stats = []
    questions = sorted(study.questions, key=lambda q: q.position)
    
    limit_val = int(study.result_count) if study.result_count else None

    for question in questions:
        stats = {
            "question_id": question.id,
            "title": question.title,
            "position": question.position,
            "type": question.questiontype.display,
            "by_type": {} 
        }
        
        # Query the Answers
        q_base = db.session.query(
            Answer.value, 
            ResultType.display, 
            Result.position,
            Answer.result_id,
            Answer.result_ai_id,
            Answer.result_chatbot_id
        ).select_from(Answer).join(
            ResultType, Answer.resulttype == ResultType.id
        ).outerjoin(
            Result, Answer.result_id == Result.id
        ).filter(
            Answer.study_id == study.id,
            Answer.question_id == question.id,
            Answer.status == 1,
            Answer.value.isnot(None)
        )

        if study.participants:
            q_base = q_base.filter(Answer.participant_id.isnot(None))
            
        results = q_base.all()
        
        if not results: continue

        grouped_data = {} 

        # Group by result type
        for val, type_name, pos, r_id, ai_id, chat_id in results:
            if limit_val and pos is not None and pos > limit_val:
                continue 
            
            t_name = type_name if type_name else "Unknown"
            if t_name not in grouped_data:
                grouped_data[t_name] = []
            
            grouped_data[t_name].append(val)

        for type_label, values in grouped_data.items():
            type_stats = {}
            count = len(values)
            if count == 0: continue

            # 1. Categorical Questions (Charts)
            if question.questiontype.display in ('likert_scale', 'true_false', 'multiple_choice'):
                options_map = {opt.value: opt.label for opt in question.options}
                counts = {}
                
                if question.questiontype.display == 'multiple_choice':
                    for v in values:
                        if v:
                            for opt in v.split(','):
                                counts[opt] = counts.get(opt, 0) + 1
                else:
                    for v in values:
                        counts[v] = counts.get(v, 0) + 1
                
                type_stats['distribution'] = sorted([
                    {"value": v, "label": options_map.get(v, v), "count": c, "percentage": (c / count) * 100}
                    for v, c in counts.items()
                ], key=lambda x: x['count'], reverse=True)
                
                if question.questiontype.display == 'likert_scale':
                    are_numeric = all(opt.value.replace('.', '', 1).isdigit() for opt in question.options if opt.value)
                    if are_numeric:
                        nums = [float(v) for v in values if v and v.replace('.', '', 1).isdigit()]
                        if nums:
                            n = len(nums)
                            m = sum(nums) / n
                            var = sum([((x - m) ** 2) for x in nums]) / n
                            type_stats['numeric_stats'] = {"mean": m, "std_dev": var ** 0.5, "count": n}

            # 2. Numeric Questions (Charts)
            elif question.questiontype.display == 'scale_number':
                nums = [float(v) for v in values if v and v.replace('.', '', 1).isdigit()]
                if nums:
                    n = len(nums)
                    type_stats['numeric_stats'] = {
                        "count": n, "mean": sum(nums)/n, "min": min(nums), "max": max(nums)
                    }
                    type_stats['raw_values'] = nums
            
            # 3. Text/Comment Questions (Scrollable List)
            # If it's not a chartable question, we assume it's text/comments
            else:
                text_answers = [str(v).strip() for v in values if v and str(v).strip()]
                if text_answers:
                    type_stats['comments'] = text_answers
            
            stats['by_type'][type_label] = type_stats

        if stats['by_type']:
            all_question_stats.append(stats)
            
    return all_question_stats if all_question_stats else None

def convert_answer_stats_to_df(answer_stats_data):
    if not answer_stats_data:
        return pd.DataFrame()

    rows = []
    for question in answer_stats_data:
        q_title = question['title']
        q_type = question['type']
        
        for type_name, type_data in question.get('by_type', {}).items():
            
            if q_type in ('likert_scale', 'true_false', 'multiple_choice'):
                for item in type_data.get('distribution', []):
                    rows.append({
                        'Question': q_title,
                        'Result Type': type_name,
                        'Type': q_type,
                        'Answer Label': item['label'],
                        'Answer Value': item.get('value', ''),
                        'Count': item['count'],
                        'Share (%)': f"{item['percentage']:.2f}"
                    })
            elif q_type == 'scale_number':
                stats = type_data.get('numeric_stats', {})
                for key, value in stats.items():
                    rows.append({
                        'Question': q_title,
                        'Result Type': type_name,
                        'Type': q_type,
                        'Answer Label': key.capitalize(),
                        'Answer Value': f"{value:.2f}" if isinstance(value, float) else value,
                        'Count': '',
                        'Share (%)': ''
                    })
    
    df = pd.DataFrame(rows)
    cols = ['Question', 'Result Type', 'Type', 'Answer Label', 'Answer Value', 'Count', 'Share (%)']
    cols = [c for c in cols if c in df.columns]
    df = df[cols] if not df.empty else df
    return df

def get_overlap_stats(study):
    """
    Berechnet die Überschneidungen (Overlap) zwischen verschiedenen Suchmaschinen
    basierend auf den URLs der Ergebnisse (nutzt jetzt die engine_text der Extension).
    """
    # 1. Finde alle existierenden Suchmaschinen in dieser Studie
    engines = db.session.query(Result.engine_text).filter(
        Result.study_id == study.id, 
        Result.engine_text.isnot(None)
    ).distinct().all()
    
    engines = [e[0] for e in engines if e[0]]
    
    # Überschneidungen machen erst ab 2 Suchmaschinen Sinn
    if len(engines) <= 1:
        return None

    se_list = {}
    for engine_str in engines:
        # Lade alle URLs für diese spezifische Suchmaschine
        q = db.session.query(Result.normalized_url).filter(
            Result.study_id == study.id,
            Result.engine_text == engine_str
        )
        
        # Tiefenlimit der Studie anwenden (z.B. nur Top 10)
        if study.result_count:
            q = q.filter(Result.position <= int(study.result_count))

        urls = {r.normalized_url for r in q.all() if r.normalized_url is not None}
        
        if urls:
            # Schönen Namen formatieren (z.B. google_us_en -> Google (US / EN))
            parts = engine_str.split('_')
            if len(parts) >= 3:
                nice_name = f"{parts[0].capitalize()} ({parts[1].upper()} / {parts[2].upper()})"
            else:
                nice_name = engine_str.replace('_', ' ').title()
                
            se_list[nice_name] = {"Sources": urls}
    
    # 2. Überschneidungen (Overlap) der Sets berechnen
    if len(se_list) > 1:
        overlap_list = []
        for (name1, data1), (name2, data2) in combinations(se_list.items(), 2):
            k = f"{name1}-{name2}"
            only_1 = len(data1["Sources"] - data2["Sources"])
            only_2 = len(data2["Sources"] - data1["Sources"])
            overlap_val = len(data1["Sources"].intersection(data2["Sources"]))
            total = len(data1["Sources"].union(data2["Sources"]))
            
            overlap_list.append({
                "SE_Pair": k, 
                "SE_1": name1, 
                "SE_1 exclusive": only_1,
                "SE_2": name2, 
                "SE_2 exclusive": only_2, 
                "Overlap": overlap_val, 
                "Total": total
            })
        return overlap_list
    
    return None