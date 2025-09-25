from .. import app, db
from ..models import (Study, Scraper, Answer, Result, ResultAi, ResultSource, 
                      Classifier, ClassifierResult, ResultAiSource, ResultType, ResultChatbot)
from sqlalchemy import func, or_, and_
from ..helpers import percentage_calc
import pandas as pd

def get_result_stats(study):
    # --- PHASE 1: Scraper-Fortschritt ---
    scrapers_all = db.session.query(Scraper.id).filter(Scraper.study_id == study.id).count()
    scrapers_done = db.session.query(Scraper.id).filter(
        Scraper.study_id == study.id,
        or_(Scraper.progress == 1, and_(Scraper.progress == -1, Scraper.counter > 10))
    ).count()
    scraper_percent = (scrapers_done / scrapers_all) * 100 if scrapers_all > 0 else 0

    # --- PHASE 2: Source-Fortschritt (falls relevant) ---
    def get_scraper_type(engine_name): # Helferfunktion
        parts = engine_name.split('_')
        return parts[-1].strip() if len(parts) > 2 and parts[-1].strip() else 'Organic'

    has_organic_engine = any(get_scraper_type(se.name) == 'Organic' for se in study.searchengines)
    
    collection_status_percent = scraper_percent # Standardwert ist nur Phase 1

    if study.studytype.id != 6 and has_organic_engine:
        # Die Basis für Phase 2 ist die Gesamtzahl aller gefundenen Standard-Ergebnisse.
        total_results_to_process = db.session.query(Result.id).filter(Result.study_id == study.id).count()
        
        finished_sources = db.session.query(ResultSource.result_id).join(Result).filter(
            Result.study_id == study.id,
            or_(ResultSource.progress == 1, and_(ResultSource.progress == -1, ResultSource.counter > 2))
        ).count()

        # FINALE BERECHNUNG: Konsistent mit der Logik in study.py.
        total_tasks = scrapers_all + total_results_to_process
        finished_tasks = scrapers_done + finished_sources
        
        if total_tasks > 0:
            collection_status_percent = (finished_tasks / total_tasks) * 100
        # Fallback, falls Scraper fertig sind, aber keine Quellen erzeugt wurden
        elif scrapers_done == scrapers_all and scrapers_all > 0:
            collection_status_percent = 100
        else:
            collection_status_percent = 0

    result_stats = {
        "Queries": len(study.queries),
        "Search Engines": len(study.searchengines),
        "Results to Collect per Query": study.result_count,
        # Der neue, korrekte Wert wird hier verwendet
        "Collection Status": f"{round(collection_status_percent)}%"
    }

    # Zähle ALLE erfassten Standard-Ergebnisse (wird jetzt oben für die %-Berechnung wiederverwendet)
    raw_results_count = db.session.query(Result.id).filter(Result.study_id == study.id).count()
    if raw_results_count > 0:
        result_stats["Total Standard Results Found"] = raw_results_count

    # Zähle die Ergebnisse MIT VERARBEITETEN QUELLEN (nur für relevante Studientypen)
    if study.studytype.id != 6:
        processed_results_count = db.session.query(Result.id)\
            .join(Result.source_associations)\
            .filter(Result.study_id == study.id, ResultSource.progress == 1)\
            .distinct().count()
        
        if processed_results_count > 0:
            result_stats["Results with Processed Source"] = processed_results_count

    ai_results_count = db.session.query(ResultAi).filter(ResultAi.study_id == study.id).count()
    if ai_results_count > 0:
        result_stats["AI Overviews Collected"] = ai_results_count

    # NEU: Zähle die Chatbot-Ergebnisse
    chatbot_results_count = db.session.query(ResultChatbot).filter(ResultChatbot.study_id == study.id).count()
    if chatbot_results_count > 0:
        result_stats["Chatbot Results Collected"] = chatbot_results_count
        
    return result_stats


def get_evaluation_stats(study):
    """
    Computes statistics related to evaluations, including a breakdown
    of completed evaluations by ResultType and a count of skipped items.
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
    
    # Zähle die verschiedenen Antwort-Status
    evals_done_answers = evals.filter(Answer.status == 1).count()
    evals_skipped_answers = evals.filter(Answer.status == 2).count()
    evals_all_answers = evals.count()
    
    # Der "fertige" Status beinhaltet nun abgeschlossene UND übersprungene Antworten
    evals_finished_answers = evals_done_answers + evals_skipped_answers
    evals_stat = percentage_calc(evals_finished_answers, evals_all_answers, "str")

    # Umrechnung von der Anzahl der Antworten zur Anzahl der bewerteten Items
    skipped_items = evals_skipped_answers // num_questions

    evaluation_stats = {
        "Participants": len(study.participants),
        "Questions": num_questions,
        "Evaluation Status": evals_stat,
        "Evaluations Skipped": skipped_items # Neue Zeile für die Statistik
    }
    
    # Die Breakdown-Abfrage bleibt unverändert, da sie nur abgeschlossene (status=1) Items zählt
    breakdown_query = db.session.query(
        ResultType.display,
        func.count(Answer.id)
    ).join(
        ResultType, Answer.resulttype == ResultType.id
    ).filter(
        Answer.study_id == study.id,
        Answer.status == 1
    ).group_by(
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


def get_classifier_stats(study):
    """
    Computes statistics for all classifiers associated with a study, including
    the relative share of total results for each classification value.
    """
    if not study.classifier:
        return None

    # Ermittle die Gesamtzahl der Standard-Ergebnisse in der Studie als Basis für die %-Berechnung
    total_results_in_study = db.session.query(Result.id).filter(Result.study_id == study.id).count()

    all_classifier_stats = {}

    for classifier in study.classifier:
        value_counts = db.session.query(
            ClassifierResult.value,
            func.count(ClassifierResult.id)
        ).join(
            Result, ClassifierResult.result_id == Result.id
        ).filter(
            Result.study_id == study.id,
            ClassifierResult.classifier_id == classifier.id
        ).group_by(
            ClassifierResult.value
        ).order_by(
            func.count(ClassifierResult.id).desc()
        ).all()

        if value_counts:
            # NEUE DATENSTRUKTUR: Speichere Anzahl und Prozentwert
            stats_dict = {}
            for value, count in value_counts:
                stats_dict[value] = {
                    "count": count,
                    "percentage": (count / total_results_in_study) * 100 if total_results_in_study > 0 else 0
                }
            all_classifier_stats[classifier.display_name] = stats_dict
            
    return all_classifier_stats if all_classifier_stats else None


def get_top_main_domains(study, limit=10): # HINZUGEFÜGT: optionales limit=10
    """
    Calculates the top 'main' domains, including their
    average position. Can be limited to a specific number.
    """
    top_domains_data = {}

    # --- Teil 1: Top Domains für Standard-Ergebnisse (Result) ---
    total_results_with_main = db.session.query(Result.id).filter(
        Result.study_id == study.id, Result.main.isnot(None)
    ).count()

    if total_results_with_main > 0:
        query = db.session.query(
            Result.main,
            func.count(Result.id).label('count'),
            func.avg(Result.position).label('avg_pos')
        ).filter(
            Result.study_id == study.id,
            Result.main.isnot(None)
        ).group_by(Result.main).order_by(func.count(Result.id).desc())

        # Wende das Limit nur an, wenn es angegeben ist
        if limit:
            query = query.limit(limit)

        top_standard_results = query.all()

        top_domains_data['standard_results'] = [
            {
                "domain": domain,
                "count": count,
                "percentage": (count / total_results_with_main) * 100,
                "avg_position": avg_pos
            } for domain, count, avg_pos in top_standard_results
        ]

    # --- Teil 2: Top Domains für AI-Quellen (ResultAiSource) ---
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
        
        # Wende das Limit nur an, wenn es angegeben ist
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
    Erstellt eine statistische Auswertung für jede Frage in der Studie.
    Die Auswertungsmethode hängt vom Fragentyp ab.
    Für Likert-Skalen werden, falls numerisch, auch Durchschnittswerte berechnet.
    """
    if not study.questions:
        return None

    all_question_stats = []
    questions = sorted(study.questions, key=lambda q: q.position)

    for question in questions:
        stats = {
            "question_id": question.id,
            "title": question.title,
            "position": question.position,
            "type": question.questiontype.display
        }
        
        answers_query = db.session.query(Answer.value).filter(
            Answer.study_id == study.id,
            Answer.question_id == question.id,
            Answer.status == 1,
            Answer.value.isnot(None)
        )

        # --- Kategoriale Fragen ---
        if question.questiontype.display in ('likert_scale', 'true_false', 'multiple_choice'):
            options_map = {opt.value: opt.label for opt in question.options}
            answer_counts = {}
            answers = answers_query.all()

            if not answers: continue

            # Zähle Antworten basierend auf ihrem Roh-Wert ('value')
            if question.questiontype.display == 'multiple_choice':
                for answer_tuple in answers:
                    if answer_tuple[0]:
                        selected_options = answer_tuple[0].split(',')
                        for option_value in selected_options:
                            answer_counts[option_value] = answer_counts.get(option_value, 0) + 1
            else:
                for answer_tuple in answers:
                    value = answer_tuple[0]
                    answer_counts[value] = answer_counts.get(value, 0) + 1
            
            # Berechne Gesamtanzahl für Prozentrechnung
            total_answers = sum(answer_counts.values())
            
            # Erstelle die Verteilungsliste und speichere Wert UND Label
            if total_answers > 0:
                stats['distribution'] = sorted([
                    {"value": value, "label": options_map.get(value, value), "count": count, "percentage": (count / total_answers) * 100}
                    for value, count in answer_counts.items()
                ], key=lambda x: x['count'], reverse=True)

            # --- Zusatz-Logik für Likert-Skalen bleibt gleich ---
            if question.questiontype.display == 'likert_scale':
                are_values_numeric = all(opt.value.replace('.', '', 1).isdigit() for opt in question.options if opt.value)
                if are_values_numeric:
                    numeric_answers = [float(a[0]) for a in answers if a[0] is not None and a[0].replace('.', '', 1).isdigit()]
                    if numeric_answers:
                        count = len(numeric_answers)
                        mean = sum(numeric_answers) / count
                        variance = sum([((x - mean) ** 2) for x in numeric_answers]) / count
                        stats['numeric_stats'] = {"mean": mean, "std_dev": variance ** 0.5}

        # --- Fall für Numerische Skalenfragen bleibt gleich ---
        elif question.questiontype.display == 'scale_number':
            numeric_values = [float(v[0]) for v in answers_query.all() if v[0] and v[0].replace('.', '', 1).isdigit()]
            if not numeric_values: continue
            
            count = len(numeric_values)
            stats['numeric_stats'] = {
                "count": count,
                "mean": sum(numeric_values) / count,
                "min": min(numeric_values),
                "max": max(numeric_values)
            }
            stats['raw_values'] = numeric_values

        if 'distribution' in stats or 'numeric_stats' in stats:
            all_question_stats.append(stats)
            
    return all_question_stats if all_question_stats else None


def convert_answer_stats_to_df(answer_stats_data):
    """ 
    Wandelt die aggregierten Antwort-Statistiken in ein sauberes
    Pandas DataFrame für den Excel-Export um.
    Enthält jetzt eine zusätzliche Spalte für den numerischen Wert.
    """
    if not answer_stats_data:
        return pd.DataFrame()

    rows = []
    for question in answer_stats_data:
        q_title = question['title']
        q_type = question['type']

        if q_type in ('likert_scale', 'true_false', 'multiple_choice'):
            for item in question.get('distribution', []):
                rows.append({
                    'Question': q_title,
                    'Type': q_type,
                    'Answer Label': item['label'],
                    'Answer Value': item.get('value', ''), # NEUE SPALTE
                    'Count': item['count'],
                    'Share (%)': f"{item['percentage']:.2f}"
                })
        elif q_type == 'scale_number':
            stats = question.get('numeric_stats', {})
            for key, value in stats.items():
                rows.append({
                    'Question': q_title,
                    'Type': q_type,
                    'Answer Label': key.capitalize(), # Hier ist es die Statistik-Art
                    'Answer Value': f"{value:.2f}" if isinstance(value, float) else value, # Hier ist es der Statistik-Wert
                    'Count': '',
                    'Share (%)': ''
                })
    
    # Sortiere Spalten für eine saubere Ausgabe
    df = pd.DataFrame(rows)
    cols = ['Question', 'Type', 'Answer Label', 'Answer Value', 'Count', 'Share (%)']
    df = df[cols]
    return df