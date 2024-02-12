# coding: utf-8
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Answer(db.Model):
    __tablename__ = 'answer'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    result = db.Column(db.ForeignKey(
        'result.id', ondelete='SET NULL'), index=True)
    value = db.Column(db.Text, nullable=False)
    question = db.Column(db.ForeignKey(
        'question.id', ondelete='CASCADE'), nullable=False, index=True)

    question1 = db.relationship(
        'Question',
        primaryjoin='Answer.question == Question.id',
        backref='answers')
    result1 = db.relationship(
        'Result', primaryjoin='Answer.result == Result.id', backref='answers')


class Evaluation(db.Model):
    __tablename__ = 'evaluation'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    comment = db.Column(db.Text, nullable=False)
    status = db.Column(db.Integer)
    source = db.Column(db.ForeignKey(
        'source.id', ondelete='SET NULL'), index=True)

    source1 = db.relationship(
        'Source',
        primaryjoin='Evaluation.source == Source.id',
        backref='evaluations')


class Option(db.Model):
    __tablename__ = 'option'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    value = db.Column(db.Text, nullable=False)
    label = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer)
    question = db.Column(db.ForeignKey(
        'question.id', ondelete='SET NULL'), index=True)

    question1 = db.relationship(
        'Question',
        primaryjoin='Option.question == Question.id',
        backref='options')


class Query(db.Model):
    __tablename__ = 'query'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    name = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=False)
    query_text = db.Column(db.Text, name='query', nullable=False)

    scraper = db.relationship(
        'Scraper', secondary='query_scraper', backref='queries')
    study = db.relationship(
        'Study', secondary='query_study', backref='queries')


t_query_scraper = db.Table(
    'query_scraper',
    db.Column('query', db.ForeignKey('query.id'),
              primary_key=True, nullable=False),
    db.Column('scraper', db.ForeignKey('scraper.id'),
              primary_key=True, nullable=False, index=True)
)


t_query_study = db.Table(
    'query_study',
    db.Column('query', db.ForeignKey('query.id'),
              primary_key=True, nullable=False),
    db.Column('study', db.ForeignKey('study.id'),
              primary_key=True, nullable=False, index=True)
)


class Question(db.Model):
    __tablename__ = 'question'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    question__type = db.Column(db.ForeignKey(
        'question_type.id', ondelete='CASCADE'), nullable=False, index=True)
    study = db.Column(db.ForeignKey(
        'study.id', ondelete='CASCADE'), nullable=False, index=True)

    question_type = db.relationship(
        'QuestionType',
        primaryjoin='Question.question__type == QuestionType.id',
        backref='questions')
    study1 = db.relationship(
        'Study', primaryjoin='Question.study == Study.id', backref='questions')
    question_template = db.relationship(
        'QuestionTemplate',
        secondary='question_question_template',
        backref='questions')


t_question_question_template = db.Table(
    'question_question_template',
    db.Column('question', db.ForeignKey('question.id'),
              primary_key=True, nullable=False),
    db.Column('question_template', db.ForeignKey(
        'question_template.id'), primary_key=True, nullable=False, index=True)
)


class QuestionTemplate(db.Model):
    __tablename__ = 'question_template'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)


class QuestionType(db.Model):
    __tablename__ = 'question_type'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    name = db.Column(db.Text, nullable=False)
    display = db.Column(db.Text)


class Reporting(db.Model):
    __tablename__ = 'reporting'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    result_count = db.Column(db.Integer)
    duplicate_count = db.Column(db.Integer)
    missing_count = db.Column(db.Integer)
    exit_condition = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    scraper = db.Column(db.ForeignKey(
        'scraper.id', ondelete='SET NULL'), index=True)

    scraper1 = db.relationship(
        'Scraper',
        primaryjoin='Reporting.scraper == Scraper.id',
        backref='reportings')


class Result(db.Model):
    __tablename__ = 'result'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    url = db.Column(db.Text, nullable=False)
    query = db.Column(db.ForeignKey(
        'query.id', ondelete='CASCADE'), nullable=False, index=True)
    scraper = db.Column(db.ForeignKey(
        'scraper.id', ondelete='CASCADE'), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False)
    main = db.Column(db.Text)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    ip = db.Column(db.Text)
    origin = db.Column(db.Text)
    serp = db.Column(db.ForeignKey(
        'serp.id', ondelete='CASCADE'), nullable=False, index=True)
    source = db.Column(db.ForeignKey(
        'source.id', ondelete='CASCADE'), nullable=False, index=True)
    hash = db.Column(db.Text)

    query1 = db.relationship(
        'Query', primaryjoin='Result.query == Query.id', backref='results')
    scraper1 = db.relationship(
        'Scraper',
        primaryjoin='Result.scraper == Scraper.id',
        backref='results')
    serp1 = db.relationship(
        'Serp', primaryjoin='Result.serp == Serp.id', backref='results')
    source1 = db.relationship(
        'Source', primaryjoin='Result.source == Source.id', backref='results')
    search_engine = db.relationship(
        'SearchEngine', secondary='result_search_engine', backref='results')
    study = db.relationship(
        'Study', secondary='result_study', backref='results')


t_result_search_engine = db.Table(
    'result_search_engine',
    db.Column('result', db.ForeignKey('result.id'),
              primary_key=True, nullable=False),
    db.Column('search_engine', db.ForeignKey('search_engine.id'),
              primary_key=True, nullable=False, index=True)
)


t_result_study = db.Table(
    'result_study',
    db.Column('result', db.ForeignKey('result.id'),
              primary_key=True, nullable=False),
    db.Column('study', db.ForeignKey('study.id'),
              primary_key=True, nullable=False, index=True)
)


class Scraper(db.Model):
    __tablename__ = 'scraper'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    progress = db.Column(db.Integer, nullable=False)
    limit = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=False)
    error_code = db.Column(db.Integer)

    search_engine = db.relationship(
        'SearchEngine', secondary='scraper_search_engine', backref='scrapers')
    study = db.relationship(
        'Study', secondary='scraper_study', backref='scrapers')


t_scraper_search_engine = db.Table(
    'scraper_search_engine',
    db.Column('scraper', db.ForeignKey('scraper.id'),
              primary_key=True, nullable=False),
    db.Column('search_engine', db.ForeignKey('search_engine.id'),
              primary_key=True, nullable=False, index=True)
)


t_scraper_study = db.Table(
    'scraper_study',
    db.Column('scraper', db.ForeignKey('scraper.id'),
              primary_key=True, nullable=False),
    db.Column('study', db.ForeignKey('study.id'),
              primary_key=True, nullable=False, index=True)
)


class SearchEngine(db.Model):
    __tablename__ = 'search_engine'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    name = db.Column(db.Text, nullable=False)
    config = db.Column(db.Text, nullable=False)

    study = db.relationship(
        'Study', secondary='search_engine_study', backref='search_engines')


t_search_engine_study = db.Table(
    'search_engine_study',
    db.Column('search_engine', db.ForeignKey('search_engine.id'),
              primary_key=True, nullable=False),
    db.Column('study', db.ForeignKey('study.id'),
              primary_key=True, nullable=False, index=True)
)


class Serp(db.Model):
    __tablename__ = 'serp'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    page = db.Column(db.Integer, nullable=False)
    code = db.Column(db.Text, nullable=False)
    img = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)


class Source(db.Model):
    __tablename__ = 'source'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    code = db.Column(db.LargeBinary, nullable=False)
    bin = db.Column(db.LargeBinary, nullable=False)
    url = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.Text)
    error_code = db.Column(db.Text)
    status_code = db.Column(db.Integer)
    final_url = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False)
    hash = db.Column(db.Text)


class Study(db.Model):
    __tablename__ = 'study'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    name = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime)
    description = db.Column(db.Text, nullable=False)
    imported = db.Column(db.Boolean)

    study_type = db.relationship(
        'StudyType', secondary='study_study_type', backref='studies')


t_study_study_type = db.Table(
    'study_study_type',
    db.Column('study', db.ForeignKey('study.id'),
              primary_key=True, nullable=False),
    db.Column('study_type', db.ForeignKey('study_type.id'),
              primary_key=True, nullable=False, index=True)
)


class StudyType(db.Model):
    __tablename__ = 'study_type'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    name = db.Column(db.Text, nullable=False)


class Trend(db.Model):
    __tablename__ = 'trend'

    id = db.Column(db.Integer, primary_key=True,
                   server_default=db.FetchedValue())
    query = db.Column(db.Text, nullable=False)
    traffic = db.Column(db.Integer, nullable=False)
    related_queries = db.Column(db.Text, nullable=False)
    sample_article = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    country = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
