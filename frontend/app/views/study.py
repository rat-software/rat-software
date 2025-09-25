from .. import app, db
from ..forms import StudyForm, ConfirmationForm
from ..models import (Study, StudyType, ResultType, SearchEngine, Query, Scraper, Answer, 
                      Result, Source, Classifier, User, RangeStudy, StudyURLFilter, 
                      Country, ResultAi, ResultSource, ResultChatbot)
from flask import Blueprint, render_template, flash, redirect, url_for, request, abort
from markupsafe import Markup
from sqlalchemy.orm import raiseload, joinedload
from flask_security import login_required, current_user, roles_accepted
from datetime import datetime
import pandas as pd
from io import BytesIO
import json
from flask_simplelogin import is_logged_in
from sqlalchemy.sql.expression import func
from sqlalchemy import text, or_, and_
import time
from flask import jsonify

@app.route('/study/<int:id>/progress')
@login_required
def study_progress(id):
    """
    Provides study progress data with adaptive 1-stage or 2-stage calculation.
    """
    study = Study.query.get_or_404(id)
    
    if study.status != 0:
        # --- TEIL 1: PRÜFEN, OB NOCH JOBS LAUFEN ---
        running_scrapers_condition = or_(
            Scraper.progress.in_([0, 2]),
            and_(Scraper.progress == -1, Scraper.counter <= 10)
        )
        running_scrapers = Scraper.query.filter(Scraper.study_id == id, running_scrapers_condition).count()

        running_standard_sources = 0
        if study.studytype.id != 6:
            running_sources_condition = or_(
                ResultSource.progress.in_([0, 2]),
                # KORREKTUR: Die Bedingung wurde von <= 3 auf <= 2 geändert, um konsistent zu sein.
                and_(ResultSource.progress == -1, ResultSource.counter <= 2)
            )
            running_standard_sources = db.session.query(Result.id).join(Result.source_associations).filter(
                Result.study_id == id, running_sources_condition
            ).distinct().count()

        # --- TEIL 2: STATUS AKTUALISIEREN ---
        if running_scrapers == 0 and running_standard_sources == 0:
            # Wenn nichts mehr läuft -> Finalen Status bestimmen
            scraper_hard_errors = Scraper.query.filter(
                Scraper.study_id == id, and_(Scraper.progress == -1, Scraper.counter > 10)
            ).count()
            source_hard_errors = 0
            if study.studytype.id != 6:
                source_hard_errors = db.session.query(Result.id).join(Result.source_associations).filter(
                    Result.study_id == id, and_(ResultSource.progress == -1, ResultSource.counter > 2)
                ).distinct().count()
            no_results_scrapers = Scraper.query.filter(
                Scraper.study_id == id, and_(Scraper.progress == -1, Scraper.counter == 11)
            ).count()

            new_status = None
            # KORREKTUR: Die Logik zur Bestimmung des finalen Status, inkl. -5, wurde hinzugefügt.
            if scraper_hard_errors > 0 and source_hard_errors > 0:
                new_status = -5
            elif scraper_hard_errors > 0:
                new_status = -2
            elif source_hard_errors > 0:
                new_status = -4
            elif no_results_scrapers > 0:
                new_status = -3
            else:
                new_status = 2
            
            if new_status is not None and new_status != study.status:
                study.status = new_status
                db.session.commit()
                db.session.refresh(study)
        else:
            # Wenn noch etwas läuft -> Status auf 1 oder -1 setzen
            temp_scraper_errors = Scraper.query.filter(Scraper.study_id == id, Scraper.progress == -1, Scraper.counter <= 10).count()
            temp_source_errors = 0
            if study.studytype.id != 6:
                temp_source_errors = db.session.query(Result.id).join(Result.source_associations).filter(
                    Result.study_id == id, ResultSource.progress == -1, 
                    # KORREKTUR: Auch hier die Bedingung von <= 3 auf <= 2 geändert.
                    ResultSource.counter <= 2
                ).distinct().count()
            
            if temp_scraper_errors > 0 or temp_source_errors > 0:
                if study.status != -1:
                    study.status = -1
                    db.session.commit()
            else:
                if study.status != 1:
                    study.status = 1
                    db.session.commit()

    # --- TEIL 3: FORTSCHRITTSDATEN ZUSAMMENSTELLEN (unverändert) ---
    # (Der Rest der Funktion zur Berechnung der Prozentzahl und der Ergebnisse bleibt gleich)
    total_scrapers = Scraper.query.filter(Scraper.study_id == id).count()
    finished_scrapers = Scraper.query.filter(
        Scraper.study_id == id, 
        or_(
            Scraper.progress == 1,
            and_(Scraper.progress == -1, Scraper.counter > 10)
        )
    ).count()

    scraper_percent = 0
    if total_scrapers > 0:
        scraper_percent = (finished_scrapers / total_scrapers) * 100

    total_progress = 0

    def get_scraper_type(engine_name):
        parts = engine_name.split('_')
        if len(parts) > 2 and parts[-1].strip():
            return parts[-1].strip()
        return 'Organic'

    has_organic_engine = any(get_scraper_type(se.name) == 'Organic' for se in study.searchengines)
    
    if study.studytype.id == 6 or not has_organic_engine:
        total_progress = scraper_percent
    else:
        total_results_to_process = db.session.query(Result.id).filter(Result.study_id == id).count()
        finished_sources = db.session.query(ResultSource.result_id).join(Result).filter(
            Result.study_id == id,
            or_(
                ResultSource.progress == 1,
                and_(ResultSource.progress == -1, ResultSource.counter > 2)
            )
        ).count()

        total_tasks = total_scrapers + total_results_to_process
        finished_tasks = finished_scrapers + finished_sources
        
        if total_tasks > 0:
            total_progress = (finished_tasks / total_tasks) * 100
        elif finished_scrapers == total_scrapers and total_scrapers > 0:
            total_progress = 100

    results = 0; results_ai = 0; results_chatbot = 0
    if study.studytype.id != 6:
        results = db.session.query(Result.id).join(Result.source_associations).filter(
            Result.study_id == id, ResultSource.progress == 1
        ).distinct().count()
    else:
        results = db.session.query(Result).filter(Result.study_id == id).count()
    results_ai = db.session.query(ResultAi).where(ResultAi.study_id == id).count()
    results_chatbot = db.session.query(ResultChatbot).where(ResultChatbot.study_id == id).count()
    
    return jsonify({
        'status': study.status, 
        'studytype_id': study.studytype.id, 
        'results': results,
        'results_ai': results_ai, 
        'results_chatbot': results_chatbot,
        'urls_collected': results,
        'progress_percent': round(total_progress)
    })

@app.route('/studies', methods=['GET', 'POST'])
@login_required
@roles_accepted('Admin')
def studies():
    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Study).order_by(Study.id.desc()).paginate(page, per_page=10)
    return render_template('studies/studies.html', pagination=pagination)


@app.route('/study/<id>')
@login_required
def study(id):
    study = Study.query.get_or_404(id)
    base = request.url_root

    try:
        if study.status != 0:
            running_scrapers_condition = or_(
                Scraper.progress.in_([0, 2]),
                and_(Scraper.progress == -1, Scraper.counter <= 10)
            )
            running_scrapers = Scraper.query.filter(Scraper.study == study, running_scrapers_condition).count()

            running_standard_sources = 0
            if study.studytype.id != 6:
                running_sources_condition = or_(
                    ResultSource.progress.in_([0, 2]),
                    # ▼▼▼ HIER IST DIE KORREKTUR ▼▼▼
                    and_(ResultSource.progress == -1, ResultSource.counter <= 2) # War vorher <= 3
                )
                running_standard_sources = db.session.query(Result.id).join(Result.source_associations).filter(
                    Result.study == study, running_sources_condition
                ).distinct().count()

            if running_scrapers == 0 and running_standard_sources == 0:
                scraper_hard_errors = Scraper.query.filter(Scraper.study_id == id, and_(Scraper.progress == -1, Scraper.counter > 10)).count()
                source_hard_errors = 0
                if study.studytype.id != 6:
                    source_hard_errors = db.session.query(Result.id).join(Result.source_associations).filter(
                        Result.study_id == id, and_(ResultSource.progress == -1, ResultSource.counter > 2)
                    ).distinct().count()
                no_results_scrapers = Scraper.query.filter(Scraper.study_id == id, and_(Scraper.progress == -1, Scraper.counter == 11)).count()

                new_status = None
                # ▼▼▼ NEUE LOGIK ▼▼▼
                # Priorität 1: Wenn BEIDE Fehlertypen vorliegen, setze den neuen Status -5
                if scraper_hard_errors > 0 and source_hard_errors > 0:
                    new_status = -5
                # ▼▼▼ Bestehende Logik als elif-Kette ▼▼▼
                elif scraper_hard_errors > 0:
                    new_status = -2
                elif source_hard_errors > 0:
                    new_status = -4
                elif no_results_scrapers > 0:
                    new_status = -3
                else:
                    new_status = 2
                
                if new_status is not None and new_status != study.status:
                    study.status = new_status
                    db.session.commit()
                    # In study_progress() kann diese Zeile nötig sein: db.session.refresh(study)
            else:
                temp_scraper_errors = Scraper.query.filter(Scraper.study == study, Scraper.progress == -1, Scraper.counter <= 10).count()
                temp_source_errors = 0
                if study.studytype.id != 6:
                    temp_source_errors = db.session.query(Result.id).join(Result.source_associations).filter(
                        Result.study == study, ResultSource.progress == -1, 
                        # ▼▼▼ HIER IST DIE ZWEITE KORREKTUR ▼▼▼
                        ResultSource.counter <= 2 # War vorher <= 3
                    ).distinct().count()
                
                if temp_scraper_errors > 0 or temp_source_errors > 0:
                    if study.status != -1:
                        study.status = -1
                        db.session.commit()
                else:
                    if study.status != 1:
                        study.status = 1
                        db.session.commit()
        
        answer_progress = Answer.query.filter(Answer.study == study, Answer.status == 0, Answer.source_status_code == 200).count()
        if study.status in [2, -3] and answer_progress == 0:
             study.status = 3
             db.session.commit()
        
        results = 0; results_ai = 0; results_chatbot = 0
        if study.studytype.id != 6:
            results = db.session.query(Result.id).join(Result.source_associations).filter(
                Result.study_id == id, ResultSource.progress == 1
            ).distinct().count()
            results_ai = db.session.query(ResultAi).where(ResultAi.study == study).count()
            results_chatbot = db.session.query(ResultChatbot).where(ResultChatbot.study == study).count()
        else:
            results = db.session.query(Result).filter(Result.study == study).count()

        max_results = sum([s.limit for s in study.scrapers]) if study.scrapers else 0
        r_pct = round(results / max_results * 100) if max_results != 0 else 0
        answers = Answer.query.filter(Answer.study == study, Answer.status != 0).count()
        max_answers = Answer.query.filter(Answer.study == study).count()
        a_pct = round(answers / max_answers * 100) if max_answers != 0 else 0

    except Exception as e:
        print(e)
        abort(500)

    # Ermitteln Sie die "Collected Result Types" aus den Suchmaschinen der Studie
    collected_type_names = set()
    for engine in study.searchengines:
        parts = engine.name.split('_')
        type_name = 'Organic'  # Standard
        if len(parts) > 2 and parts[-1] in ['AI', 'Chatbot']:
            type_name = parts[-1]
        collected_type_names.add(type_name)

    # Holen Sie die vollständigen ResultType-Objekte aus der Datenbank
    collected_result_types_ = ResultType.query.filter(ResultType.name.in_(list(collected_type_names))).all()

    return render_template('studies/study.html', 
                           study=study, 
                           results=results, 
                           results_ai=results_ai, 
                           results_chatbot=results_chatbot, 
                           max_results=max_results, 
                           r_pct=r_pct, 
                           answers=answers, 
                           max_answers=max_answers, 
                           a_pct=a_pct, 
                           base=base,
                           collected_result_types_=collected_result_types_)

@app.route('/study/new', methods=['GET', 'POST'])
@login_required
def new_study():
    form = StudyForm()
    title = "Create Study"
    all_engines = SearchEngine.query.filter_by(test=1).order_by(SearchEngine.name).all()
    providers = sorted(list(set([engine.name.split('_')[0] for engine in all_engines])))
    locations = sorted([c[0] for c in Country.query.with_entities(Country.code).distinct().order_by(Country.code).all()])
    
    scraper_to_assessment_name_map = {}
    search_result_filter_options = []
    for rt_filter in ResultType.query.filter_by(filter=True).all():
        scraper_identifier = rt_filter.name.replace(" Results", "").replace(" Overview", "").strip()
        if scraper_identifier:
            scraper_to_assessment_name_map[scraper_identifier] = rt_filter.name
            search_result_filter_options.append((scraper_identifier, rt_filter.display))
            
    assessment_result_types = ResultType.query.filter_by(selection=True).all()
    study_type_choices = [
        {"id": str(s.id), "name": s.name, "description": s.description}
        for s in StudyType.query.order_by(StudyType.id.asc()).all()
    ]
    form.type.choices = []
    form.classifiers.choices = [(str(s.id), s.display_name) for s in Classifier.query.filter_by(display=True).all()]

    return render_template('studies/new_study.html', 
                           form=form, 
                           title=title, 
                           search_engines=all_engines, 
                           providers=providers, 
                           locations=locations, 
                           search_result_types=search_result_filter_options,
                           assessment_result_types=assessment_result_types,
                           scraper_to_assessment_name_map=scraper_to_assessment_name_map,
                           study_type_choices=study_type_choices)

@app.route('/study/new/confirm', methods=['GET', 'POST'])
@login_required
def confirm_new_study():
    confirm = ConfirmationForm()
    if request.method == "POST":
        form_data = dict(request.form.lists())
        files = request.files
        query_filename = files.get("query_list").filename if files.get("query_list") else ""

        engines_ = [SearchEngine.query.get_or_404(id) for id in form_data.get("search_engines", [])]
        classifiers_ = [Classifier.query.get_or_404(id) for id in form_data.get("classifiers", [])]
        
        search_key = 'ranges'
        res = dict(filter(lambda item: search_key in item[0], form_data.items()))
        ranges_dict = {}
        if res and res.get('ranges-0-start_range') and res['ranges-0-start_range'][0]:
            ranges_counter, ranges_number = 0, 0
            for key, value in res.items():
                if ranges_counter % 2:
                    ranges_dict[ranges_number]["end"] = value[0]
                    ranges_number += 1
                else:
                    ranges_dict[ranges_number] = {"start": value[0]}
                ranges_counter += 1
        
        type_ = StudyType.query.get_or_404(form_data["type"][0])
        
        assessment_result_type_ids = form_data.get("assessment_result_types", [])

        if type_.id != 6 and not assessment_result_type_ids:
            flash('You must select at least one "Result Type" for assessment in Step 4.', 'danger')
            return redirect(url_for('new_study'))

        assessment_result_types_ = ResultType.query.filter(ResultType.id.in_(assessment_result_type_ids)).all()
        
        # ▼▼▼▼▼▼▼▼▼▼▼▼ HIER IST DER NEUE CODE-BLOCK ▼▼▼▼▼▼▼▼▼▼▼▼
        # 1. Ermitteln Sie die einzigartigen Typ-Namen aus den ausgewählten Suchmaschinen
        collected_type_names = set()
        for engine in engines_:
            parts = engine.name.split('_')
            type_name = 'Organic'  # Standard-Typ
            # Überschreiben, wenn ein spezifischer Typ wie 'AI' oder 'Chatbot' im Namen ist
            if len(parts) > 2 and parts[-1] in ['AI', 'Chatbot']:
                type_name = parts[-1]
            collected_type_names.add(type_name)

        # 2. Holen Sie die vollständigen ResultType-Objekte aus der Datenbank
        collected_result_types_ = ResultType.query.filter(ResultType.name.in_(list(collected_type_names))).all()
        # ▲▲▲▲▲▲▲▲▲▲▲▲ ENDE DES NEUEN CODE-BLOCKS ▲▲▲▲▲▲▲▲▲▲▲▲
        
        queries_ = []
        if form_data.get("queries") and form_data["queries"][0]:
            for query in form_data["queries"][0].splitlines():
                if query.strip():
                    queries_.append({"query": query, "limit": form_data["result_count"], "source": 'text'})
        
        form_data["queries"] = queries_
        show_urls = "show_urls" in form_data
        show_ai_sources = "show_ai_sources" in form_data

        limit_per_participant = "limit_per_participant" in form_data
        max_results_per_participant = form_data.get("max_results_per_participant", [""])[0]

        url_filter_include_ = [inc for inc in form_data.get("url_filter_include", [""])[0].splitlines() if inc]
        url_filter_exclude_ = [exc for exc in form_data.get("url_filter_exclude", [""])[0].splitlines() if exc]

        return render_template('studies/confirm_new_study.html', 
                               form=form_data, 
                               confirm=confirm, 
                               engines_=engines_, 
                               classifiers_=classifiers_, 
                               type_=type_, 
                               assessment_result_types_=assessment_result_types_, 
                               queries_=queries_, 
                               query_filename=query_filename, 
                               ranges_ = ranges_dict, 
                               show_urls = show_urls, 
                               url_filter_include = url_filter_include_, 
                               url_filter_exclude = url_filter_exclude_,
                               limit_per_participant=limit_per_participant, 
                               max_results_per_participant=max_results_per_participant, 
                               show_ai_sources=show_ai_sources,
                               collected_result_types_=collected_result_types_) # <-- NEUE VARIABLE HINZUGEFÜGT
    
    return redirect(url_for('new_study'))


@app.route('/study/new/create/', methods=['GET', 'POST'])
@login_required
def create_new_study():
    data = dict(request.form)
    data_json_str = data["data"].replace("'", '"')
    dt = json.loads(data_json_str)
    study_id = int(dt['id'][0])
    
    if study_id == 0:
        study = Study(
            name=dt["name"][0], status=0, description=dt["description"][0],
            studytype=StudyType.query.get_or_404(int(dt["type"][0])),
            imported=False, result_count=int(dt["result_count"][0]),
            task=dt["task"][0], created_at=datetime.now(), 
            show_urls=bool(dt.get("show_urls")),
            show_ai_sources=bool(dt.get("show_ai_sources")),
            limit_per_participant=bool(dt.get("limit_per_participant")),
            max_results_per_participant=int(dt["max_results_per_participant"][0]) if dt.get("limit_per_participant") else None
        )
        db.session.add(study)
        study.queries.extend([Query(query=q["query"], limit=int(q["limit"][0] if isinstance(q["limit"], list) else q["limit"]), created_at=datetime.now()) for q in dt["queries"]])
        study.searchengines.extend([SearchEngine.query.get_or_404(int(engine)) for engine in dt.get("search_engines", [])])
        if classifiers_data := dt.get("classifiers"):
            study.classifier.extend([Classifier.query.get_or_404(int(c)) for c in classifiers_data])
        study.users.extend([current_user] + [User.query.get(id) for id in [19, 8] if current_user.id != id and User.query.get(id)])
        if result_type_ids := dt.get("assessment_result_types"):
            result_types_to_add = ResultType.query.filter(ResultType.id.in_(result_type_ids)).all()
            study.assessment_result_types.extend(result_types_to_add)
        db.session.commit()

        search_key = 'ranges'
        res = dict(filter(lambda item: search_key in item[0], dt.items()))
        if res and res.get('ranges-0-start_range') and res.get('ranges-0-start_range')[0]:
            ranges_dict = {}
            ranges_counter, ranges_number = 0, 0
            for key, value in res.items():
                if ranges_counter % 2:
                    ranges_dict[ranges_number]["end"] = value[0]; ranges_number += 1
                else: ranges_dict[ranges_number] = {"start": value[0]}
                ranges_counter += 1
            for key, value in ranges_dict.items():
                if value.get('start') and value.get('end'):
                    db.session.add(RangeStudy(study=study.id, range_start=value['start'], range_end=value['end']))

        for url in dt.get("url_filter_include", []):
            if url: db.session.add(StudyURLFilter(study_id=study.id, url=url, include=True, exclude=False))
        for url in dt.get("url_filter_exclude", []):
            if url: db.session.add(StudyURLFilter(study_id=study.id, url=url, include=False, exclude=True))
        
        db.session.commit()
        flash('Your study has been created.', 'success')
        return redirect(url_for('study', id=study.id))

    else:
        study = Study.query.get_or_404(study_id)
        study.name = dt["name"][0]; study.task = dt["task"][0]; study.description = dt["description"][0]
        if result_type_ids := dt.get("assessment_result_types"):
            result_types_to_update = ResultType.query.filter(ResultType.id.in_(result_type_ids)).all()
            study.assessment_result_types = result_types_to_update
        else:
            study.assessment_result_types = []
        study.result_count = int(dt["result_count"][0]); study.updated_at = datetime.now()
        study.show_urls = bool(dt.get("show_urls"))
        study.show_ai_sources = bool(dt.get("show_ai_sources"))
        study.limit_per_participant = bool(dt.get("limit_per_participant"))
        study.max_results_per_participant = int(dt["max_results_per_participant"][0]) if study.limit_per_participant else None
        db_queries = {q.query: q for q in study.queries}
        frm_queries = {q["query"]: q for q in dt["queries"]}
        for q_text, q_obj in db_queries.items():
            if q_text not in frm_queries: db.session.delete(q_obj)
        for q_text, q_data in frm_queries.items():
            if q_text not in db_queries: study.queries.append(Query(query=q_text, limit=int(dt["result_count"][0]), created_at=datetime.now()))
        study.searchengines[:] = [SearchEngine.query.get_or_404(int(se_id)) for se_id in dt.get("search_engines", [])]
        existing_includes = {f.url for f in study.study_url_filters if f.include}
        existing_excludes = {f.url for f in study.study_url_filters if f.exclude}
        new_includes = set(filter(None, dt.get("url_filter_include", [])))
        new_excludes = set(filter(None, dt.get("url_filter_exclude", [])))
        if urls_to_remove := (existing_includes - new_includes) | (existing_excludes - new_excludes):
            StudyURLFilter.query.filter(StudyURLFilter.study_id == study.id, StudyURLFilter.url.in_(urls_to_remove)).delete(synchronize_session=False)
        for url in new_includes - existing_includes: db.session.add(StudyURLFilter(study_id=study.id, url=url, include=True, exclude=False))
        for url in new_excludes - existing_excludes: db.session.add(StudyURLFilter(study_id=study.id, url=url, include=False, exclude=True))
        RangeStudy.query.filter_by(study=study.id).delete()
        search_key = 'ranges'
        res = dict(filter(lambda item: search_key in item[0], dt.items()))
        if res and res.get('ranges-0-start_range') and res.get('ranges-0-start_range')[0]:
            ranges_dict = {}
            ranges_counter, ranges_number = 0, 0
            for key, value in res.items():
                if ranges_counter % 2:
                    ranges_dict[ranges_number]["end"] = value[0]; ranges_number += 1
                else: ranges_dict[ranges_number] = {"start": value[0]}
                ranges_counter += 1
            for key, value in ranges_dict.items():
                if value.get('start') and value.get('end'):
                    db.session.add(RangeStudy(study=study.id, range_start=value['start'], range_end=value['end']))
        db.session.commit()
        flash('Your study has been updated.', 'success')
        return redirect(url_for('study', id=study.id))

@app.route('/study/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_study(id):
    study = Study.query.get_or_404(id)
    form = StudyForm(obj=study)
    title = f"Edit Study: {study.name}"
    if request.method == 'POST':
        return redirect(url_for('study', id=id))
    all_engines = SearchEngine.query.filter_by(test=1).order_by(SearchEngine.name).all()
    providers = sorted(list(set([engine.name.split('_')[0] for engine in all_engines])))
    locations = sorted([c[0] for c in Country.query.with_entities(Country.code).distinct().order_by(Country.code).all()])
    scraper_to_assessment_name_map = {}
    search_result_filter_options = []
    for rt_filter in ResultType.query.filter_by(filter=True).all():
        scraper_identifier = rt_filter.name.replace(" Results", "").replace(" Overview", "").strip()
        if scraper_identifier:
            scraper_to_assessment_name_map[scraper_identifier] = rt_filter.name
            search_result_filter_options.append((scraper_identifier, rt_filter.display))
    assessment_result_types = ResultType.query.filter_by(selection=True).all()
    study_type_choices = [
        {"id": str(s.id), "name": s.name, "description": s.description}
        for s in StudyType.query.order_by(StudyType.id.asc()).all()
    ]
    form.type.choices = []    
    form.classifiers.choices = [(str(s.id), s.display_name) for s in Classifier.query.filter_by(display=True).all()]
    form.id.data = study.id
    form.name.data = study.name
    form.description.data = study.description
    form.task.data = study.task
    form.type.data = str(study.studytype_id)
    form.result_count.data = study.result_count
    form.show_urls.data = study.show_urls
    form.show_ai_sources.data = study.show_ai_sources
    form.limit_per_participant.data = study.limit_per_participant
    form.max_results_per_participant.data = study.max_results_per_participant
    form.queries.data = '\n'.join([q.query for q in study.queries])
    form.search_engines.data = [s.id for s in study.searchengines]
    form.assessment_result_types.data = [rt.id for rt in study.assessment_result_types]
    form.url_filter_include.data = '\n'.join([f.url for f in study.study_url_filters if f.include])
    form.url_filter_exclude.data = '\n'.join([f.url for f in study.study_url_filters if f.exclude])
    while form.ranges.entries:
        form.ranges.pop_entry()
    ranges_from_db = RangeStudy.query.filter_by(study=study.id).all()
    for r in ranges_from_db:
        form.ranges.append_entry({
            'start_range': r.range_start,
            'end_range': r.range_end
        })
    return render_template('studies/new_study.html', 
                           form=form, 
                           study=study, 
                           title=title, 
                           search_engines=all_engines, 
                           providers=providers, 
                           locations=locations, 
                           search_result_types=search_result_filter_options,
                           assessment_result_types=assessment_result_types,
                           scraper_to_assessment_name_map=scraper_to_assessment_name_map,
                           study_type_choices=study_type_choices)

@app.route('/study/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete_study(id):
    study = Study.query.get_or_404(id)
    form = ConfirmationForm()
    if request.method == 'POST':
        # NUR DIESE ZEILE IST NÖTIG
        db.session.delete(study)
        
        db.session.commit()
        flash('Study deleted successfully.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('studies/delete_study.html', form=form, study=study)

@app.route('/study/<id>/close')
@login_required
def close_study(id):
    study = Study.query.get_or_404(id)
    study.status = 4
    db.session.commit()
    flash('Study closed. Thank you for using RAT', 'success')
    return redirect(url_for("study", id=id))