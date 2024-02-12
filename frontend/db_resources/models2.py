# coding: utf-8
from . import db


class Query(db.Model):
    __tablename__ = 'queries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    study_id = db.Column(db.Integer, db.ForeignKey('studies.id'))
    study = db.relationship("Study", back_populates="queries")

    results = db.relationship("Result", back_populates="query")
    scrapers = db.relationship("Scraper", back_populates="query")
    serps = db.relationship("Serp", back_populates="query")


class Reporting(db.Model):
    __tablename__ = 'reporting'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    total_result_count = db.Column(db.Integer, nullable=False)
    duplicate_result_count = db.Column(db.Integer, nullable=False)
    missing_values_count = db.Column(db.Integer, nullable=False)
    exit_condition = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, nullable=False)

    scrapers = db.relationship("Scraper", back_populates="reporting")


class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, nullable=False)
    url = db.Column(db.Text, nullable=False)
    main = db.Column(db.Text)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False)
    ip = db.Column(db.Text)
    results_hash = db.Column(db.Text)
    origin = db.Column(db.Text)

    search_engine_id = db.Column(db.Integer, db.ForeignKey('search_engines.id'))
    search_engine = db.relationship("SearchEngine", back_populates="results")

    query_id = db.Column(db.Integer, db.ForeignKey('queries.id'))
    query = db.relationship("Query", back_populates="results")

    scraper_id = db.Column(db.Integer, db.ForeignKey('scrapers.id'))
    scraper = db.relationship("Scrapers", back_populates="results")

    study_id = db.Column(db.Integer, db.ForeignKey('studies.id'))
    study = db.relationship("Studies", back_populates="results")


class Scraper(db.Model):
    __tablename__ = 'scrapers'

    id = db.Column(db.Integer, primary_key=True)
    results_limit = db.Column(db.Integer)
    progress = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    error_code = db.Column(db.Integer, nullable=False)
    counter = db.Column(db.Integer)

    reporting_id = db.Column(db.Integer, db.ForeignKey('reporting.id'))
    reporting = db.relationship("Reporting", back_populates="scraper")

    search_engine_id = db.Column(db.Integer, db.ForeignKey('search_engines.id'))
    search_engine = db.relationship("SearchEngine", back_populates="scrapers")

    study_id = db.Column(db.Integer, db.ForeignKey('studies.id'))
    study = db.relationship("Studies", back_populates="scrapers")

    query_id = db.Column(db.Integer, db.ForeignKey('queries.id'))
    query = db.relationship("Query", back_populates="scrapers")

    results = db.relationship("Result", back_populates="scraper")


class SearchEngine(db.Model):
    __tablename__ = 'search_engines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    config = db.Column(db.Text, nullable=False)

    results = db.relationship("Result", back_populates="search_engine")
    scrapers = db.relationship("Scraper", back_populates="search_engine")
    serps = db.relationship("Serp", back_populates="search_engine")


class Serp(db.Model):
    __tablename__ = 'serps'

    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.Integer, nullable=False)
    code = db.Column(db.Text, nullable=False)
    img = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    query_id = db.Column(db.Integer, db.ForeignKey('queries.id'))
    query = db.relationship("Query", back_populates="serps")

    study_id = db.Column(db.Integer, db.ForeignKey('studies.id'))
    study = db.relationship("Study", back_populates="serps")

    search_engine_id = db.Column(db.Integer, db.ForeignKey('search_engines.id'))
    search_engine = db.relationship("SearchEngine", back_populates="serps")


class Source(db.Model):
    __tablename__ = 'sources'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.LargeBinary)
    bin = db.Column(db.LargeBinary)
    timestamp = db.Column(db.DateTime, nullable=False)
    url = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Integer, nullable=False)
    mime = db.Column(db.Text, nullable=False)
    error_code = db.Column(db.Text)
    status_code = db.Column(db.Integer)
    final_url = db.Column(db.Text)

    results_hash = db.Column(db.Text, nullable=False, unique=True)


class Study(db.Model):
    __tablename__ = 'studies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    search_engines = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False)
    imported = db.Column(db.Boolean, nullable=False)

    queries = db.relationship("Query", back_populates="study")
    results = db.relationship("Result", back_populates="study")
    scrapers = db.relationship("Scraper", back_populates="study")
    serps = db.relationship("Serp", back_populates="study")

    type_id = db.Column(db.Integer, db.ForeignKey('study_types.id'))
    type = db.relationship("StudyType", back_populates="studies")


class StudyType(db.Model):
    __tablename__ = 'study_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    studies = db.relationship("Study", back_populates="type")


class Trend(db.Model):
    __tablename__ = 'trends'

    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.Text, nullable=False)
    traffic = db.Column(db.Integer, nullable=False)
    related_queries = db.Column(db.Text)
    sample_article = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    country = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    date_collected = db.Column(db.DateTime, nullable=False)
