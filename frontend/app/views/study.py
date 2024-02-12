from .. import app, db
from ..forms import StudyForm, ConfirmationForm
from ..models import Study, StudyType, ResultType, SearchEngine, Query, Scraper, Answer, Result, Source, Classifier, User
from flask import render_template, flash, redirect, url_for, request, abort, Markup
from sqlalchemy.orm import raiseload, joinedload
from flask_security import login_required, current_user, roles_accepted
from datetime import datetime
import pandas as pd
from io import BytesIO
import json


@app.route('/studies', methods=['GET', 'POST'])
@login_required
@roles_accepted('Admin')
def studies():
    page = request.args.get('page', 1, type=int)
    pagination = db.session.query(Study).order_by(
        Study.id).paginate(page, per_page=10)

    return render_template('studies/studies.html',
                           pagination=pagination)


@app.route('/study/<id>')
@login_required
def study(id):
    try:
        study = Study.query.get_or_404(id)

        base = request.url_root

        scraper_progress = Scraper.query.filter(Scraper.study == study).filter(Scraper.progress == 0 & 2).count()
        source_progress = Result.query.filter(Result.study == study).filter(Result.sources.any(Source.progress == 0 & 2)).count()
        answer_progress = Answer.query.filter(Answer.study == study).filter((Answer.status == 0) & (Answer.source_status_code == 200)).count()

        scraper_error = Scraper.query.filter(Scraper.study == study).filter(Scraper.progress == -1).count()

        # status 2: results AND sources collected

        if (study.status != 4) & (study.status != 0):
            if (source_progress == 0) & (scraper_progress == 0):
                study.status = 2
                db.session.commit()
            # study status 3: assessments finished
            if (source_progress == 0) & (answer_progress == 0):#
                if scraper_error > 0:
                    study.status = -1
                else:
                    study.status = 3
                db.session.commit()


        # get results info
        results = db.session.query(Result).join(Result.sources).where((Source.status_code == 200) & (Source.progress == 1)).where(Result.study == study).count()
        max_results = sum([s.limit for s in study.scrapers])
        r_pct = round(results / max_results * 100) if max_results != 0 else 0

        # get answers info
        answers = Answer.query.filter(
            Answer.study == study, Answer.status != 0).count()
        max_answers = Answer.query.filter(Answer.study == study).count()
        a_pct = round(answers / max_answers * 100) if max_answers != 0 else 0

    except Exception as e:
        print(e)
        abort(500)

    return render_template('studies/study.html',
                           study=study,
                           results=results,
                           max_results=max_results,
                           r_pct=r_pct,
                           answers=answers,
                           max_answers=max_answers,
                           a_pct=a_pct,
                           base=base)


@app.route('/study/new', methods=['GET', 'POST'])
@login_required
def new_study():
    form = StudyForm()
    title = "Create Study"

    # gets study types from db to populate form selection
    form.type.choices = [(str(s.id), s.name)
                         for s in StudyType.query.all()]

    # gets search engines from db to populate form selection
    form.search_engines.choices = [(str(s.id), s.name)
                                   for s in SearchEngine.query.filter(SearchEngine.test == 1).order_by(SearchEngine.provider.asc(), SearchEngine.resulttype.asc(), SearchEngine.country.asc()).all()]

    return render_template('studies/new_study.html',
                           form=form,
                           title=title)


@app.route('/study/new/confirm', methods=['GET', 'POST'])
@login_required
def confirm_new_study():
    confirm = ConfirmationForm()

    if request.method == "POST":

        form = dict(request.form.lists())
        files = request.files
        query_filename = files["query_list"].filename
        print(form)

        # get search engines
        engines_ = []
        engine_ls = []
        if "search_engines" in form:
            for id in form["search_engines"]:
                e = SearchEngine.query.get_or_404(id)
                engines_.append(e)
                engine_ls.append(id)

        # get study type
        type_ = StudyType.query.get_or_404(form["type"][0])

        # get result type
        result_type_ = ResultType.query.get_or_404(form["result_type"][0])
        print(result_type_)
        # get queries
        queries_ = []
        query_ls = []

        # from text box
        if form["queries"] != [""]:
            for query in form["queries"][0].splitlines():
                q = {}
                q["query"] = query
                q["limit"] = form["result_count"] if form["result_count"] else 10
                q["source"] = 'text'

                queries_.append(q)

        # from file upload
        else:
            # check if file is csv or excel
            content_type = ["text/csv",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]

            if files["query_list"].content_type in content_type:
                bytes_data = files["query_list"].read()

                # read csv
                if files["query_list"].content_type == content_type[0]:
                    df = pd.read_csv(BytesIO(bytes_data))

                # read excel
                elif files["query_list"].content_type == content_type[1]:
                    df = pd.read_excel(BytesIO(bytes_data))

                for row in df.to_dict(orient="records"):
                    print(row)
                    q = {}
                    q["query"] = row["Query"]
                    q["limit"] = row["Limit"] if row["Limit"] else form["result_count"]
                    q["source"] = 'upload'

                    queries_.append(q)

            else:
                flash("Uploaded file is invalid.", "error")

        form["queries"] = queries_
        print(form)
        return render_template('studies/confirm_new_study.html',
                               form=form,
                               confirm=confirm,
                               engines_=engines_,
                               type_=type_,
                               queries_=queries_,
                               result_type_=result_type_,
                               query_filename=query_filename,
                               query_ls=query_ls,
                               engine_ls=engine_ls)


@app.route('/study/new/create/', methods=['GET', 'POST'])
@login_required
def create_new_study():
    data = dict(request.form)
    data = data["data"].replace("'", '"')
    print(data)
    dt = json.loads(data)

    id = int(dt['id'][0])

    if id == 0:

        new_queries = []
        for query in dt["queries"]:
            print(query)
            q = Query()
            q.query = query["query"]
            if query["source"] == "upload":
                q.limit = int(query["limit"])
            else:
                q.limit = int(query["limit"][0])
            q.created_at = datetime.now()

            new_queries.append(q)

        new_engines = []
        for engine in dt["search_engines"]:
            id = int(engine)
            e = SearchEngine.query.get_or_404(id)

            new_engines.append(e)

        new_type = StudyType.query.get_or_404(int(dt["type"][0]))
        new_result_type = ResultType.query.get_or_404(
            int(dt["result_type"][0]))

        classifier = Classifier.query.get_or_404(1)

        study = Study()
        study.name = dt["name"][0]
        study.status = 0
        study.description = dt["description"][0]
        study.studytype = new_type
        study.resulttype = new_result_type
        study.queries.extend(new_queries)
        study.searchengines.extend(new_engines)
        study.imported = False
        study.result_count = int(dt["result_count"][0])
        study.task = dt["task"][0]
        study.created_at = datetime.now()

        study.classifier.append(classifier)

        user_list = [current_user]
        if current_user.id != 31:
            admin1 = User.query.get(31)
            user_list.append(admin1)
        if current_user.id != 19:
            admin2 = User.query.get(19)
            user_list.append(admin2)

        study.users.extend(user_list)


        insert = []
        insert.extend(new_queries)
        insert.append(study)

        db.session.add_all(insert)
        db.session.commit()

        flash('Your study has been created.', 'success')
        return redirect(url_for('study', id=study.id))

    else:
        study = Study.query.get_or_404(id)

        # queries
        query_add = []
        query_drop = []

        db_queries = [q.query for q in study.queries]
        frm_queries = [q["query"] for q in dt["queries"]]

        # generate list of queries to add
        for q in frm_queries:
            if q not in db_queries:
                query_add.append(q)

        # generate list of queries to drop
        for q in db_queries:
            if q not in frm_queries:
                query_drop.append(q)

        # drop queries
        for query in study.queries:
            if query.query in query_drop:
                db.session.delete(query)

        # create new queries
        updated_queries = []
        for query in query_add:
            q = Query()
            q.query = query
            q.limit = int(dt["result_count"][0])
            q.created_at = datetime.now()

            updated_queries.append(q)

        # search engines
        frm_se = [int(se) for se in dt["search_engines"]]
        db_se = [se.id for se in study.searchengines]

        se_all = SearchEngine.query.all()

        for se in se_all:
            if se.id in frm_se and se.id not in db_se:
                study.searchengines.append(se)
            if se.id not in frm_se and se.id in db_se:
                study.searchengines.remove(se)

        new_type = StudyType.query.get_or_404(int(dt["type"][0]))
        new_result_type = ResultType.query.get_or_404(
            int(dt["result_type"][0]))

        # update entry
        study.name = dt["name"][0]
        study.task = dt["task"][0]
        study.description = dt["description"][0]
        study.studytype = new_type
        study.resulttype = new_result_type
        study.queries.extend(updated_queries)
        study.imported = False
        study.result_count = int(dt["result_count"][0])
        study.updated_at = datetime.now()

        db.session.commit()

        flash('Your study has been updated.', 'success')
        return redirect(url_for('study', id=study.id))


@app.route('/study/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete_study(id):
    # are you sure you want to delete? y/n
    study = Study.query.get_or_404(id)
    form = ConfirmationForm()

    print(study.scrapers)
    print(study.queries)
    print(study)

    if form.is_submitted():
        if form.submit.data:
            # delete scrapers_
            for scraper in study.scrapers:
                db.session.delete(scraper)

            # delete queries
            for query in study.queries:
                db.session.delete(query)

            # delete study
            db.session.delete(study)

            # commit to db
            db.session.commit()

            flash('Study deleted', 'success')
            return redirect(url_for('dashboard'))

    return render_template('studies/delete_study.html',
                           form=form,
                           study=study)


@app.route('/study/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_study(id):
    study = Study.query.get_or_404(id)
    form = StudyForm()

    title = "Edit Study"

    form.id.data = study.id
    form.name.data = study.name
    form.task.data = study.task
    form.description.data = study.description
    form.type.choices = [(str(s.id), s.name)
                         for s in StudyType.query.filter(StudyType.id <= 2)]
    form.type.data = study.studytype.id
    form.search_engines.choices = [(str(s.id), s.name)
                                   for s in SearchEngine.query.filter(SearchEngine.id <= 2)]
    form.search_engines.data = [s.id for s in study.searchengines]
    form.queries.data = '\n'.join([q.query for q in study.queries])
    form.result_type.data = study.resulttype.id
    form.result_count.data = study.result_count

    return render_template('studies/new_study.html',
                           form=form,
                           study=study,
                           title=title)


@app.route('/study/<id>/close')
@login_required
def close_study(id):

    study = Study.query.get_or_404(id)
    study.status = 4
    db.session.commit()

    flash('Study closed. Thank you for using RAT', 'success')
    return redirect(url_for("study", id=id))
