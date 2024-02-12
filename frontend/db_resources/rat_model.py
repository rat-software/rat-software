# coding: utf-8
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()



class Query(db.Model):
    __tablename__ = 'queries'
    __table_args__ = (
        db.Index('queries_query_studies_id_idx', 'query', 'studies_id'),
    )

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    query = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    studies_id = db.Column(db.Integer, nullable=False)



class Reporting(db.Model):
    __tablename__ = 'reporting'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    timestamp = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())
    scraper_id = db.Column(db.Integer, nullable=False)
    total_result_count = db.Column(db.Integer, nullable=False)
    duplicate_result_count = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    missing_values_count = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    exit_condition = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())



class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    position = db.Column(db.Integer, nullable=False)
    url = db.Column(db.Text, nullable=False)
    main = db.Column(db.Text)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False)
    ip = db.Column(db.Text)
    results_hash = db.Column(db.Text)
    origin = db.Column(db.Text)
    search_engine_id = db.Column(db.Integer)
    queries_id = db.Column(db.Integer)
    scrapers_id = db.Column(db.Integer)
    studies_id = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())



class Scraper(db.Model):
    __tablename__ = 'scrapers'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    queries_id = db.Column(db.Integer, nullable=False)
    queries_query = db.Column(db.Text)
    results_limit = db.Column(db.Integer, server_default=db.FetchedValue())
    progress = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    timestamp = db.Column(db.DateTime, nullable=False)
    studies_id = db.Column(db.Integer, nullable=False)
    error_code = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    search_engine_id = db.Column(db.Integer, nullable=False)
    counter = db.Column(db.Integer, server_default=db.FetchedValue())



class ScrapersSearchengine(db.Model):
    __tablename__ = 'scrapers_searchengines'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.FetchedValue())
    scraper_id = db.Column(db.ForeignKey('scrapers.id'), nullable=False)
    search_engine_id = db.Column(db.ForeignKey('search_engines.id'), nullable=False)

    scraper = db.relationship('Scraper', primaryjoin='ScrapersSearchengine.scraper_id == Scraper.id', backref='scrapers_searchengines')
    search_engine = db.relationship('SearchEngine', primaryjoin='ScrapersSearchengine.search_engine_id == SearchEngine.id', backref='scrapers_searchengines')



class SearchEngine(db.Model):
    __tablename__ = 'search_engines'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    name = db.Column(db.String(255), nullable=False)
    config = db.Column(db.String(255), nullable=False)



class Serp(db.Model):
    __tablename__ = 'serps'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    queries_id = db.Column(db.Integer, nullable=False)
    queries_query = db.Column(db.Text, nullable=False)
    page = db.Column(db.Integer, nullable=False)
    code = db.Column(db.Text, nullable=False)
    img = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    studies_id = db.Column(db.Integer, nullable=False)
    search_engine_id = db.Column(db.Integer, nullable=False)



class Source(db.Model):
    __tablename__ = 'sources'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    code = db.Column(db.LargeBinary)
    bin = db.Column(db.LargeBinary)
    timestamp = db.Column(db.DateTime, nullable=False)
    url = db.Column(db.Text, nullable=False)
    progress = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    results_hash = db.Column(db.Text, nullable=False, unique=True)
    mime = db.Column(db.Text, nullable=False, server_default=db.FetchedValue())
    error_code = db.Column(db.Text)
    status_code = db.Column(db.Integer)
    final_url = db.Column(db.Text)



class Study(db.Model):
    __tablename__ = 'studies'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    search_engines = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False)
    imported = db.Column(db.Boolean, nullable=False, server_default=db.FetchedValue())
    study_type = db.Column(db.ForeignKey('study_types.id'), nullable=False)

    study_type1 = db.relationship('StudyType', primaryjoin='Study.study_type == StudyType.id', backref='studies')



class StudyType(db.Model):
    __tablename__ = 'study_types'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    name = db.Column(db.String(255), nullable=False)



class Testx(db.Model):
    __tablename__ = 'testx'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    title = db.Column(db.Text)
    url = db.Column(db.Text)
    description = db.Column(db.Text)
    position = db.Column(db.Integer)
    engine = db.Column(db.Text)
    query = db.Column(db.Text)



class Trend(db.Model):
    __tablename__ = 'trends'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    query = db.Column(db.Text, nullable=False)
    traffic = db.Column(db.Integer, nullable=False)
    related_queries = db.Column(db.Text)
    sample_article = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    country = db.Column(db.Text, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    date_collected = db.Column(db.DateTime, nullable=False)
