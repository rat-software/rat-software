from .. import app, db
from ..models import (Scraper, Answer, Result, ResultAi, ResultSource, 
                      ClassifierResult, ResultAiSource, ResultType, ResultChatbot)
                      
from sqlalchemy import func, or_, and_, text
from ..helpers import percentage_calc
import pandas as pd
from itertools import combinations

def get_result_stats(study):
    from ..models import Serp  # Import Serp model inline to ensure no circular import flags
    
    # Central variable for the maximum number of scraper retries
    max_retries = 3 
    
    scrapers_all = db.session.query(Scraper.id).filter(Scraper.study_id == study.id).count()
    scrapers_done = db.session.query(Scraper.id).filter(
        Scraper.study_id == study.id,
        or_(Scraper.progress == 1, and_(Scraper.progress == -1, Scraper.counter >= max_retries)) # For initial scrapers
    ).count()
    scraper_percent = (scrapers_done / scrapers_all) * 100 if scrapers_all > 0 else 0

    total_results_to_process = db.session.query(Result.id).filter(Result.study_id == study.id).count()
    
    if study.live_link_mode:
        collection_status_display = "N/A (Live Mode)"
    else:
        collection_status_percent = scraper_percent
        if total_results_to_process > 0 or scrapers_all > 0:
            # FIXED: Counts only definitively finished (1) or definitively failed (>= max_retries) sources
            finished_sources = db.session.query(ResultSource.result_id).join(Result).filter(
                Result.study_id == study.id,
                or_(ResultSource.progress == 1, and_(ResultSource.progress == -1, ResultSource.counter >= max_retries))
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

    search_engines_count = db.session.query(Result.engine_text).filter(
        Result.study_id == study.id, 
        Result.engine_text.isnot(None)
    ).distinct().count()    

    result_stats = {
        "Queries": len(study.queries),
        "Search Engines": search_engines_count,
        "Collection Status": collection_status_display
    }

    if total_results_to_process > 0:
        result_stats["Total Standard Results Found"] = total_results_to_process

        if not study.live_link_mode:
            processed_results_count = db.session.query(Result.id)\
                .join(Result.source_associations)\
                .filter(Result.study_id == study.id, ResultSource.progress == 1)\
                .distinct().count()
            
            # FIXED: Count only definitively failed sources (reached max retries limit)
            failed_results_count = db.session.query(Result.id)\
                .join(Result.source_associations)\
                .filter(Result.study_id == study.id, ResultSource.progress == -1, ResultSource.counter >= max_retries)\
                .distinct().count()
            
            # NEW: Count sources that are currently in the retry loop
            retry_results_count = db.session.query(Result.id)\
                .join(Result.source_associations)\
                .filter(Result.study_id == study.id, ResultSource.progress == -1, ResultSource.counter < max_retries)\
                .distinct().count()
            
            if processed_results_count > 0 or failed_results_count > 0 or retry_results_count > 0:
                result_stats["Results with Processed Source"] = processed_results_count
                result_stats["Results with Failed Source"] = failed_results_count
                
                # Display this row in the dashboard as long as the scraper is still attempting retries
                if retry_results_count > 0:
                    result_stats["Sources currently in Retry"] = retry_results_count

    # --- ADDED: SERP Layout Pages Count Metric ---
    serp_results_count = db.session.query(Serp).filter(Serp.study_id == study.id).count()
    if serp_results_count > 0:
        result_stats["SERP Pages Collected"] = serp_results_count

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

    # --- 1. Organic Standard Results  ---
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

    # --- 2. AI Sources  ---
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
        
        # --- FIX: Using text() literal expressions drops implicit table entity loading ---
        q_base = db.session.query(
            Answer.value, 
            ResultType.display, 
            Result.position,
            Answer.result_id,
            Answer.result_ai_id,
            Answer.result_chatbot_id,
            text("answer.result_serp")  # Bypasses the Serp entity model class resolution completely
        ).select_from(Answer)\
         .outerjoin(ResultType, Answer.resulttype == ResultType.id)\
         .outerjoin(Result, Answer.result_id == Result.id)\
         .filter(
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
        for val, type_name, pos, r_id, ai_id, chat_id, serp_id in results:
            if limit_val and pos is not None and pos > limit_val:
                continue 
            
            # Formulates dynamic labels cleanly for the dashboard UI tabs
            if type_name:
                t_name = type_name
            elif serp_id:
                t_name = "SERP Results"
            elif chat_id:
                t_name = "Chatbots"
            elif ai_id:
                t_name = "AI Overviews"
            else:
                t_name = "Organic Results"
                
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
    Calculates the overlaps between different search engines
    based on the URLs of the results (now uses engine_text from the extension).
    """
    # 1. Identify all existing search engines in this study
    engines = db.session.query(Result.engine_text).filter(
        Result.study_id == study.id, 
        Result.engine_text.isnot(None)
    ).distinct().all()
    
    engines = [e[0] for e in engines if e[0]]
    
    # Overlaps only make sense if there are at least two search engines
    if len(engines) <= 1:
        return None

    se_list = {}
    for engine_str in engines:
        # Load all URLs for this specific search engine
        q = db.session.query(Result.normalized_url).filter(
            Result.study_id == study.id,
            Result.engine_text == engine_str
        )
        
        # Apply the depth limit for the study (e.g., top 10 only)
        if study.result_count:
            q = q.filter(Result.position <= int(study.result_count))

        urls = {r.normalized_url for r in q.all() if r.normalized_url is not None}
        
        if urls:
            # Get a nice name for the search engine
            parts = engine_str.split('_')
            if len(parts) >= 3:
                nice_name = f"{parts[0].capitalize()} ({parts[1].upper()} / {parts[2].upper()})"
            else:
                nice_name = engine_str.replace('_', ' ').title()
                
            se_list[nice_name] = {"Sources": urls}
    
    # 2. Calculate Overlaps
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
    
    
def get_query_evaluation_stats(study):
    from ..models import Serp
    # 1. Alle Queries der Studie laden
    queries = {q.id: {
        "text": q.query, "total_items": 0, 
        "finished_answers": 0, "open_answers": 0, 
        "unique_participants": set()
    } for q in study.queries}
    
    if not queries:
        return None
        
    # 2. Mapping: Welche Result-ID gehört zu welcher Query-ID?
    res_map = {r.id: r.query_id for r in db.session.query(Result.id, Result.query_id).filter_by(study_id=study.id).all()}
    ai_map = {r.id: r.query_id for r in db.session.query(ResultAi.id, ResultAi.query_id).filter_by(study_id=study.id).all()}
    chat_map = {r.id: r.query_id for r in db.session.query(ResultChatbot.id, ResultChatbot.query_id).filter_by(study_id=study.id).all()}
    serp_map = {r.id: r.query_id for r in db.session.query(Serp.id, Serp.query_id).filter_by(study_id=study.id).all()}
    
    # 3. Zähle die verfügbaren Items pro Query zusammen
    for q_id in res_map.values(): queries[q_id]["total_items"] += 1
    for q_id in ai_map.values(): queries[q_id]["total_items"] += 1
    for q_id in chat_map.values(): queries[q_id]["total_items"] += 1
    for q_id in serp_map.values(): queries[q_id]["total_items"] += 1
    
    # 4. Gehe alle Antworten durch und weise sie der Query zu
    answers = db.session.query(Answer.result_id, Answer.result_ai_id, Answer.result_chatbot_id, Answer.result_serp_id, Answer.status, Answer.participant_id).filter_by(study_id=study.id).all()
    
    for ans in answers:
        q_id = None
        if ans.result_id: q_id = res_map.get(ans.result_id)
        elif ans.result_ai_id: q_id = ai_map.get(ans.result_ai_id)
        elif ans.result_chatbot_id: q_id = chat_map.get(ans.result_chatbot_id)
        elif ans.result_serp_id: q_id = serp_map.get(ans.result_serp_id)
        
        if q_id and q_id in queries:
            if ans.status == 1: # Abgeschlossen
                queries[q_id]["finished_answers"] += 1
            if ans.status == 2: # Skipped
                queries[q_id]["finished_answers"] += 1
                if ans.participant_id: 
                    queries[q_id]["unique_participants"].add(ans.participant_id)
            elif ans.status == 0: # Offen / In Bearbeitung
                queries[q_id]["open_answers"] += 1
                
    # 5. Formatierung für das Frontend
    num_questions = len(study.questions) or 1
    result_list = []
    
    for q_id, data in queries.items():
        expected_answers = data["total_items"] * num_questions
        progress_pct = (data["finished_answers"] / expected_answers * 100) if expected_answers > 0 else 0
        
        result_list.append({
            "id": q_id,
            "query_text": data["text"],
            "items": data["total_items"],
            "participants_count": len(data["unique_participants"]),
            "finished_answers": data["finished_answers"],
            "open_answers": data["open_answers"],
            "expected_answers": expected_answers,
            "progress_pct": round(progress_pct, 1)
        })
        
    # Standard-Sortierung: Die am wenigsten bearbeiteten Queries nach oben
    result_list.sort(key=lambda x: x["progress_pct"])
    return result_list