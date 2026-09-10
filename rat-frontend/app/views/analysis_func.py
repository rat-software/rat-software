"""
Analysis Functions Module for the RAT Application.

This module provides data aggregation helper functions to calculate and structure 
various dashboard metrics, including scraping progress, participant evaluation states, 
LLM/classifier trends, top domain matrices, search engine overlap lists, 
and granular query tracking.
"""

from .. import app, db
from ..models import (Scraper, Answer, Result, ResultAi, ResultSource, 
                      ClassifierResult, ResultAiSource, ResultType, ResultChatbot, ResultImage, ClassifierIndicator)
                      
from sqlalchemy import func, or_, and_, text, case
from ..helpers import percentage_calc
import pandas as pd
from itertools import combinations
from collections import defaultdict

def get_result_stats(study):
    """
    Calculates scraping progress metrics and totals for all distinct source types.
    """
    from ..models import Serp 
    
    max_retries = 3 
    
    scrapers_all = db.session.query(Scraper.id).filter(Scraper.study_id == study.id).count()
    scrapers_done = db.session.query(Scraper.id).filter(
        Scraper.study_id == study.id,
        or_(Scraper.progress == 1, and_(Scraper.progress == -1, Scraper.counter >= max_retries)) 
    ).count()
    scraper_percent = (scrapers_done / scrapers_all) * 100 if scrapers_all > 0 else 0

    total_results_to_process = db.session.query(Result.id).filter(Result.study_id == study.id).count()
    
    if study.live_link_mode:
        collection_status_display = "N/A (Live Mode)"
    else:
        collection_status_percent = scraper_percent
        if total_results_to_process > 0 or scrapers_all > 0:
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
            
            failed_results_count = db.session.query(Result.id)\
                .join(Result.source_associations)\
                .filter(Result.study_id == study.id, ResultSource.progress == -1, ResultSource.counter >= max_retries)\
                .distinct().count()
            
            retry_results_count = db.session.query(Result.id)\
                .join(Result.source_associations)\
                .filter(Result.study_id == study.id, ResultSource.progress == -1, ResultSource.counter < max_retries)\
                .distinct().count()
            
            if processed_results_count > 0 or failed_results_count > 0 or retry_results_count > 0:
                result_stats["Results with Processed Source"] = processed_results_count
                result_stats["Results with Failed Source"] = failed_results_count
                
                if retry_results_count > 0:
                    result_stats["Sources currently in Retry"] = retry_results_count

    serp_results_count = db.session.query(Serp.id).filter(Serp.study_id == study.id).count()
    if serp_results_count > 0:
        result_stats["SERP Pages Collected"] = serp_results_count

    ai_results_count = db.session.query(ResultAi.id).filter(ResultAi.study_id == study.id).count()
    if ai_results_count > 0:
        result_stats["AI Answers Collected"] = ai_results_count

    ai_sources_count = db.session.query(ResultAiSource.id).filter(ResultAiSource.study_id == study.id).count()
    if ai_sources_count > 0:
        result_stats["Total AI Sources Found"] = ai_sources_count
        
        if not study.live_link_mode:
            processed_ai_sources = db.session.query(ResultAiSource.id)\
                .filter(ResultAiSource.study_id == study.id, ResultAiSource.progress == 1).count()
            
            failed_ai_sources = db.session.query(ResultAiSource.id)\
                .filter(ResultAiSource.study_id == study.id, ResultAiSource.progress == -1, ResultAiSource.counter >= max_retries).count()
                
            retry_ai_sources = db.session.query(ResultAiSource.id)\
                .filter(ResultAiSource.study_id == study.id, ResultAiSource.progress == -1, ResultAiSource.counter < max_retries).count()

            if processed_ai_sources > 0 or failed_ai_sources > 0 or retry_ai_sources > 0:
                result_stats["AI Sources Processed"] = processed_ai_sources
                result_stats["AI Sources Failed"] = failed_ai_sources
                
                if retry_ai_sources > 0:
                    result_stats["AI Sources currently in Retry"] = retry_ai_sources

    image_results_count = db.session.query(ResultImage.id).filter(ResultImage.study_id == study.id).count()
    if image_results_count > 0:
        result_stats["Total Image Results"] = image_results_count
        if not study.live_link_mode:
            processed_img = db.session.query(ResultImage.id).filter(ResultImage.study_id == study.id, ResultImage.progress == 1).count()
            failed_img = db.session.query(ResultImage.id).filter(ResultImage.study_id == study.id, ResultImage.progress == -1, ResultImage.counter >= max_retries).count()
            if processed_img > 0 or failed_img > 0:
                result_stats["Images Processed"] = processed_img
                result_stats["Images Failed"] = failed_img

    chatbot_results_count = db.session.query(ResultChatbot.id).filter(ResultChatbot.study_id == study.id).count()
    if chatbot_results_count > 0:
        result_stats["Chatbot Results Collected"] = chatbot_results_count
        
    return result_stats

def get_evaluation_stats(study):
    """
    Computes performance summary markers for participant questionnaire progress.
    """
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
    """
    Groups classifier output trends, supporting standard classifiers and the multi-task LLM system.
    Dynamically unpacks JSON outputs so that metrics can be grouped by individual JSON keys.
    """
    if not study.classifier or study.live_link_mode:
        return None

    all_classifier_stats = {}
    import json
    import re
    from collections import defaultdict

    def parse_llm_json(val):
        if not isinstance(val, str): return val
        v = val.strip()
        if v.startswith("```"):
            v = re.sub(r'^```[a-zA-Z]*\n?', '', v)
            v = re.sub(r'\n?```$', '', v).strip()
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            m = re.search(r'\{.*\}', v, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(0))
                except:
                    pass
        raise ValueError("No JSON found")

    for classifier in study.classifier:
        
        source_type_case = case(
            (Result.id.isnot(None), 'Organic Results'),
            (ResultAiSource.id.isnot(None), 'AI Sources'),
            (ResultAi.id.isnot(None), 'AI Answers'),
            (ResultChatbot.id.isnot(None), 'Chatbots'),
            (ResultImage.id.isnot(None), 'Images'),
            else_='Unknown'
        )

        if classifier.name == 'universal_llm':
            target_id = func.coalesce(
                ClassifierIndicator.result_id, 
                ClassifierIndicator.result_ai_source_id, 
                ClassifierIndicator.result_ai_id, 
                ClassifierIndicator.result_chatbot_id,
                ClassifierIndicator.result_image_id
            )
            
            stats_query = db.session.query(
                source_type_case.label('source_type'),
                ClassifierIndicator.indicator,
                ClassifierIndicator.value,
                func.count(target_id.distinct()) 
            ).select_from(ClassifierIndicator) \
             .outerjoin(Result, ClassifierIndicator.result_id == Result.id) \
             .outerjoin(ResultAiSource, ClassifierIndicator.result_ai_source_id == ResultAiSource.id) \
             .outerjoin(ResultAi, ClassifierIndicator.result_ai_id == ResultAi.id) \
             .outerjoin(ResultChatbot, ClassifierIndicator.result_chatbot_id == ResultChatbot.id) \
             .outerjoin(ResultImage, ClassifierIndicator.result_image_id == ResultImage.id) \
             .filter(
                ClassifierIndicator.classifier_id == classifier.id,
                or_(
                    Result.study_id == study.id,
                    ResultAiSource.study_id == study.id,
                    ResultAi.study_id == study.id,
                    ResultChatbot.study_id == study.id,
                    ResultImage.study_id == study.id,
                    ClassifierIndicator.study_id == study.id 
                )
            ).group_by(source_type_case, ClassifierIndicator.indicator, ClassifierIndicator.value).all()

            if stats_query:
                for src_type, ind_name, val, count in stats_query:
                    clean_name = ind_name.replace("LLM_", "")
                    task_key = f"LLM: {clean_name}"
                    
                    if task_key not in all_classifier_stats:
                        all_classifier_stats[task_key] = {'is_json': False, 'source_types': defaultdict(lambda: {'raw_stats': {}})}
                        
                    try:
                        parsed_val = parse_llm_json(val)
                        if isinstance(parsed_val, dict):
                            all_classifier_stats[task_key]['is_json'] = True
                            for k, v in parsed_val.items():
                                if 'keys' not in all_classifier_stats[task_key]['source_types'][src_type]:
                                    all_classifier_stats[task_key]['source_types'][src_type]['keys'] = defaultdict(lambda: defaultdict(int))
                                all_classifier_stats[task_key]['source_types'][src_type]['keys'][k][str(v)] += count
                        else:
                            raw_dict = all_classifier_stats[task_key]['source_types'][src_type]['raw_stats']
                            raw_dict[str(val)] = raw_dict.get(str(val), 0) + count
                    except ValueError:
                        raw_dict = all_classifier_stats[task_key]['source_types'][src_type]['raw_stats']
                        raw_dict[str(val)] = raw_dict.get(str(val), 0) + count

        else:
            target_id = func.coalesce(
                ClassifierResult.result_id, 
                ClassifierResult.result_ai_source_id, 
                ClassifierResult.result_ai_id, 
                ClassifierResult.result_chatbot_id,
                ClassifierResult.result_image_id
            )
            
            stats_query = db.session.query(
                source_type_case.label('source_type'),
                ClassifierResult.value,
                func.count(target_id.distinct()) 
            ).select_from(ClassifierResult) \
             .outerjoin(Result, ClassifierResult.result_id == Result.id) \
             .outerjoin(ResultAiSource, ClassifierResult.result_ai_source_id == ResultAiSource.id) \
             .outerjoin(ResultAi, ClassifierResult.result_ai_id == ResultAi.id) \
             .outerjoin(ResultChatbot, ClassifierResult.result_chatbot_id == ResultChatbot.id) \
             .outerjoin(ResultImage, ClassifierResult.result_image_id == ResultImage.id) \
             .filter(
                ClassifierResult.classifier_id == classifier.id,
                or_(
                    Result.study_id == study.id,
                    ResultAiSource.study_id == study.id,
                    ResultAi.study_id == study.id,
                    ResultChatbot.study_id == study.id,
                    ResultImage.study_id == study.id,
                    ClassifierResult.study_id == study.id 
                )
            ).group_by(source_type_case, ClassifierResult.value).all()

            if stats_query:
                task_key = classifier.display_name
                for src_type, val, count in stats_query:
                    if task_key not in all_classifier_stats:
                        all_classifier_stats[task_key] = {'is_json': False, 'source_types': defaultdict(lambda: {'raw_stats': {}})}
                        
                    try:
                        parsed_val = parse_llm_json(val)
                        if isinstance(parsed_val, dict):
                            all_classifier_stats[task_key]['is_json'] = True
                            for k, v in parsed_val.items():
                                if 'keys' not in all_classifier_stats[task_key]['source_types'][src_type]:
                                    all_classifier_stats[task_key]['source_types'][src_type]['keys'] = defaultdict(lambda: defaultdict(int))
                                all_classifier_stats[task_key]['source_types'][src_type]['keys'][k][str(v)] += count
                        else:
                            raw_dict = all_classifier_stats[task_key]['source_types'][src_type]['raw_stats']
                            raw_dict[str(val)] = raw_dict.get(str(val), 0) + count
                    except ValueError:
                        raw_dict = all_classifier_stats[task_key]['source_types'][src_type]['raw_stats']
                        raw_dict[str(val)] = raw_dict.get(str(val), 0) + count
                        
    def default_to_regular(d):
        if isinstance(d, defaultdict):
            d = {k: default_to_regular(v) for k, v in d.items()}
        return d
        
    return default_to_regular(all_classifier_stats) if all_classifier_stats else None

def get_top_main_domains(study, limit=10):
    """
    Compiles visibility matrices highlighting domain presence across standard search and AI channels.
    """
    top_domains_data = {}

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
    """
    Aggregates question options distribution details and descriptive numeric metrics.
    """
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
        
        q_base = db.session.query(
            Answer.value, 
            ResultType.display, 
            Result.position,
            Answer.result_id,
            Answer.result_ai_id,
            Answer.result_chatbot_id,
            text("answer.result_serp")
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

        for val, type_name, pos, r_id, ai_id, chat_id, serp_id in results:
            if limit_val and pos is not None and pos > limit_val:
                continue 
            
            if type_name:
                t_name = type_name
            elif serp_id:
                t_name = "SERP Results"
            elif chat_id:
                t_name = "Chatbots"
            elif ai_id:
                t_name = "AI Answers"
            else:
                t_name = "Organic Results"
                
            if t_name not in grouped_data:
                grouped_data[t_name] = []
            
            grouped_data[t_name].append(val)

        for type_label, values in grouped_data.items():
            type_stats = {}
            count = len(values)
            if count == 0: continue

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

            elif question.questiontype.display == 'scale_number':
                nums = [float(v) for v in values if v and v.replace('.', '', 1).isdigit()]
                if nums:
                    n = len(nums)
                    type_stats['numeric_stats'] = {
                        "count": n, "mean": sum(nums)/n, "min": min(nums), "max": max(nums)
                    }
                    type_stats['raw_values'] = nums
            
            else:
                text_answers = [str(v).strip() for v in values if v and str(v).strip()]
                if text_answers:
                    type_stats['comments'] = text_answers
            
            stats['by_type'][type_label] = type_stats

        if stats['by_type']:
            all_question_stats.append(stats)
            
    return all_question_stats if all_question_stats else None
    
def convert_answer_stats_to_df(answer_stats_data):
    """
    Flattens the structured question metrics dictionary format into a Pandas DataFrame.
    """
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
    Calculates intersecting URL distributions across distinct search engines.
    Heavily optimized to fetch data in bulk rather than hammering the database
    with thousands of singular queries (fixes N+1 Query Timeout Problem).
    """
    engine_rows = db.session.query(Result.engine_text).filter(
        Result.study_id == study.id, 
        Result.engine_text.isnot(None)
    ).distinct().all()
    
    engines = [e[0] for e in engine_rows if e[0]]
    
    # Overlaps only make sense if there are at least two search engines
    if len(engines) <= 1:
        return None

    def get_nice_name(engine_str):
        parts = engine_str.split('_')
        if len(parts) >= 3:
            return f"{parts[0].capitalize()} ({parts[1].upper()} / {parts[2].upper()})"
        return engine_str.replace('_', ' ').title()

    # --- SUPER OPTIMIZATION: Fetch ALL relevant URLs in ONE single bulk query ---
    q = db.session.query(Result.query_id, Result.engine_text, Result.normalized_url).filter(
        Result.study_id == study.id,
        Result.normalized_url.isnot(None)
    )
    
    if study.result_count:
        q = q.filter(Result.position <= int(study.result_count))
        
    all_results = q.all()
    
    # Build memory map: data[query_id][engine_text] = set(urls)
    query_data = defaultdict(lambda: defaultdict(set))
    for q_id, engine, url in all_results:
        query_data[q_id][engine].add(url)

    overlap_list = []
    
    # Calculate intersections PER QUERY for every search engine pair purely in Python memory
    for e1, e2 in combinations(engines, 2):
        name1 = get_nice_name(e1)
        name2 = get_nice_name(e2)
        
        total_excl_1 = 0
        total_excl_2 = 0
        total_overlap = 0
        total_union = 0
        
        for qid, engine_dict in query_data.items():
            urls1 = engine_dict.get(e1, set())
            urls2 = engine_dict.get(e2, set())
            
            # If neither engine has data for this query, skip
            if not urls1 and not urls2:
                continue
                
            # Calculate Set Math rapidly in memory
            total_excl_1 += len(urls1 - urls2)
            total_excl_2 += len(urls2 - urls1)
            total_overlap += len(urls1.intersection(urls2))
            total_union += len(urls1.union(urls2))
            
        # Only append if there is actual data compared
        if total_union > 0:
            overlap_list.append({
                "SE_Pair": f"{name1}-{name2}", 
                "SE_1": name1, 
                "SE_1 exclusive": total_excl_1,
                "SE_2": name2, 
                "SE_2 exclusive": total_excl_2, 
                "Overlap": total_overlap, 
                "Total": total_union
            })
            
    return overlap_list if overlap_list else None
    

def get_query_evaluation_stats(study):
    """
    Monitors question progress status filtered individually per query.
    Optimized mapping queries to drastically reduce SQLAlchemy object initialization overhead.
    """
    from ..models import Serp
    
    queries = {q.id: {
        "text": q.query, "total_items": 0, 
        "finished_answers": 0, "open_answers": 0, 
        "unique_participants": set()
    } for q in study.queries}
    
    if not queries:
        return None
        
    # OPTIMIZATION: Fetch tuple mappings directly to bypass slow SQLAlchemy Model loading
    res_map = {r[0]: r[1] for r in db.session.query(Result.id, Result.query_id).filter_by(study_id=study.id).all()}
    ai_map = {r[0]: r[1] for r in db.session.query(ResultAi.id, ResultAi.query_id).filter_by(study_id=study.id).all()}
    chat_map = {r[0]: r[1] for r in db.session.query(ResultChatbot.id, ResultChatbot.query_id).filter_by(study_id=study.id).all()}
    serp_map = {r[0]: r[1] for r in db.session.query(Serp.id, Serp.query_id).filter_by(study_id=study.id).all()}
    
    for q_id in res_map.values(): queries[q_id]["total_items"] += 1
    for q_id in ai_map.values(): queries[q_id]["total_items"] += 1
    for q_id in chat_map.values(): queries[q_id]["total_items"] += 1
    for q_id in serp_map.values(): queries[q_id]["total_items"] += 1
    
    # Process all answers via raw tuple projection to save memory
    answers = db.session.query(
        Answer.result_id, Answer.result_ai_id, Answer.result_chatbot_id, 
        Answer.result_serp_id, Answer.status, Answer.participant_id
    ).filter_by(study_id=study.id).all()
    
    for r_id, ai_id, chat_id, serp_id, status, p_id in answers:
        q_id = None
        if r_id: q_id = res_map.get(r_id)
        elif ai_id: q_id = ai_map.get(ai_id)
        elif chat_id: q_id = chat_map.get(chat_id)
        elif serp_id: q_id = serp_map.get(serp_id)
        
        if q_id and q_id in queries:
            if status in [1, 2]: # Completed (1) OR Skipped (2)
                queries[q_id]["finished_answers"] += 1
                if p_id: 
                    queries[q_id]["unique_participants"].add(p_id)
            elif status == 0: # Open / In Progress
                queries[q_id]["open_answers"] += 1
                
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
        
    result_list.sort(key=lambda x: x["progress_pct"])
    return result_list