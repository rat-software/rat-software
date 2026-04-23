"""
Database Models for the Result Assessment Tool (RAT).

This module defines the entire SQLAlchemy ORM schema for the application, 
handling complex relationships between studies, scraping configurations, 
collected search results, AI-generated content, and human participant assessments.
"""

from app import db
from flask_security import UserMixin, RoleMixin


# ==============================================================================
# ASSOCIATION TABLES (Many-to-Many Relationships)
# ==============================================================================
# Define association tables for many-to-many relationships

# Links participants to the studies they are assigned to evaluate
participant_study = db.Table('participant_study',
                             db.Column('participant', db.ForeignKey(
                                 'participant.id'), primary_key=True),
                             db.Column('study', db.ForeignKey(
                                 'study.id'), primary_key=True), extend_existing=True,
                             )

# Links specific questions to the results they are evaluating
question_result = db.Table('question_result',
                           db.Column('question', db.ForeignKey(
                               'question.id'), primary_key=True),
                           db.Column('result', db.ForeignKey(
                               'result.id'), primary_key=True), extend_existing=True,
                           )

# Links search engines (Google, Bing, etc.) to specific studies
searchengine_study = db.Table('searchengine_study',
                              db.Column('searchengine', db.ForeignKey(
                                  'searchengine.id'), primary_key=True),
                              db.Column('study', db.ForeignKey(
                                  'study.id'), primary_key=True), extend_existing=True,
                              )

# Links admin/researcher users to the studies they manage
study_user = db.Table('study_user',
                      db.Column('study', db.ForeignKey(
                          'study.id'), primary_key=True),
                      db.Column('user', db.ForeignKey(
                          'user.id'), primary_key=True), extend_existing=True,
                      )

# Links users to their authorization roles
user_role = db.Table('user_role',
                     db.Column('user', db.ForeignKey(
                         'user.id'), primary_key=True),
                     db.Column('role', db.ForeignKey(
                         'role.id'), primary_key=True), extend_existing=True,
                     )


# Links automated classifiers to studies
classifier_study = db.Table('classifier_study',
                         db.Column('classifier', db.ForeignKey('classifier.id')),
                         db.Column('study', db.ForeignKey('study.id')), extend_existing=True,
                         )

# Links Query Search (QS) studies to users
qs_study_user = db.Table('qs_study_user',
    db.Column('qs_study', db.Integer, db.ForeignKey('qs_study.id'), primary_key=True),
    db.Column('user', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    extend_existing=True
)

# ==============================================================================
# CORE ORM MODELS
# ==============================================================================


# Classes for Query Sampler
class Qs_Study(db.Model):
    __tablename__ = 'qs_study'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    users = db.relationship('User', secondary=qs_study_user, back_populates='qs_studies', lazy='select')
    description = db.Column(db.String, nullable=True)
    visible = db.Column(db.Boolean, default=True, nullable=False)

class Qs_Geotarget(db.Model):
    __tablename__ = 'qs_geotarget'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    canonical_name = db.Column(db.String)
    country_code = db.Column(db.String)
    target_type = db.Column(db.String)
    criterion_id = db.Column(db.Integer)

class Qs_Keyword(db.Model):
    __tablename__ = 'qs_keyword'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    qs_study_id = db.Column(db.Integer)
    qs_geotarget_criterion_id = db.Column(db.Integer)
    qs_language_code_criterion_id = db.Column(db.Integer)
    keyword = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    status = db.Column(db.Integer)

class Qs_Keyword_Idea(db.Model):
    __tablename__ = 'qs_keyword_idea'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    qs_study_id = db.Column(db.Integer)
    qs_keyword_id = db.Column(db.Integer)
    keyword_idea = db.Column(db.String)
    avg_monthly_searches = db.Column(db.Integer)
    competition = db.Column(db.String)
    created_at = db.Column(db.DateTime)

class Qs_Language_Code(db.Model):
    __tablename__ = 'qs_language_code'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    criterion_id = db.Column(db.Integer)



class Answer(db.Model):
    """Model for storing answers given by participants to questions."""
    __tablename__ = 'answer'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String)
    status = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    source_status_code = db.Column(db.Integer)
    resulttype = db.Column(db.Integer)

    participant_id = db.Column('participant', db.Integer, db.ForeignKey('participant.id'))
    participant = db.relationship('Participant', back_populates='answers', lazy='select')

    question_id = db.Column('question', db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', back_populates='answers', lazy='select')

    result_id = db.Column('result', db.Integer, db.ForeignKey('result.id'), nullable=True)
    result = db.relationship('Result', back_populates='answers', lazy='select')

    result_ai_id = db.Column('result_ai', db.Integer, db.ForeignKey('result_ai.id'), nullable=True)
    result_ai = db.relationship('ResultAi', back_populates='answers', lazy='select')

    result_chatbot_id = db.Column('result_chatbot', db.Integer, db.ForeignKey('result_chatbot.id'), nullable=True)
    result_chatbot = db.relationship('ResultChatbot', back_populates='answers', lazy='select')
    
    result_serp_id = db.Column('result_serp', db.Integer, db.ForeignKey('serp.id'), nullable=True)
    result_serp = db.relationship('Serp', back_populates='answers', lazy='select')

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='answers', lazy='select')

    result_type_text = db.Column(db.String(50), nullable=True)

    __table_args__ = (
        db.Index('idx_answer_lookup', 'participant', 'study', 'status'),
        {'extend_existing': True}
    )

class Classifier(db.Model):
    __tablename__ = 'classifier'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String)
    display_name = db.Column('display_name', db.String)
    display = db.Column(db.Boolean)
    indicators = db.relationship('ClassifierIndicator', back_populates='classifier', uselist=False, lazy='select')
    results = db.relationship('ClassifierResult', back_populates='classifier', lazy='select')
    studies = db.relationship('Study', secondary=classifier_study, back_populates='classifier', lazy='select')

class ClassifierResult(db.Model):
    __tablename__ = 'classifier_result'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    classifier_id = db.Column("classifier", db.Integer, db.ForeignKey('classifier.id'))
    result_id = db.Column("result", db.Integer, db.ForeignKey('result.id'))
    value = db.Column('value', db.String)
    created_at = db.Column(db.DateTime)
    classifier = db.relationship("Classifier", back_populates="results")
    result = db.relationship("Result", back_populates="classifier")


class ClassifierIndicator(db.Model):
    __tablename__ = 'classifier_indicator'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    indicator = db.Column('indicator', db.String)
    value = db.Column('value', db.String)
    created_at = db.Column(db.DateTime)
    result_id = db.Column('result', db.Integer, db.ForeignKey('result.id', ondelete='CASCADE'), index=True)
    result = db.relationship('Result', back_populates='indicators', lazy='select')
    classifier_id = db.Column('classifier', db.Integer, db.ForeignKey('classifier.id'))
    classifier = db.relationship('Classifier', back_populates='indicators', lazy='select')


class StudyURLFilter(db.Model):
    __tablename__ = 'study_url_filter'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='study_url_filters', lazy='select')
    url = db.Column(db.String)
    include = db.Column(db.Boolean)
    exclude = db.Column(db.Boolean)


class Option(db.Model):
    __tablename__ = 'option'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String)
    label = db.Column(db.String)
    position = db.Column(db.Integer)
    question_id = db.Column('question', db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', back_populates='options', lazy='select')


class Participant(db.Model):
    __tablename__ = 'participant'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    password = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    answers = db.relationship('Answer', back_populates='participant', lazy='select')
    studies = db.relationship('Study', secondary=participant_study, back_populates='participants', lazy='select')


class Query(db.Model):
    __tablename__ = 'query'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String)
    description = db.Column(db.String)
    limit = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='queries', lazy='select')
    source_type = db.Column(db.String(50), default='manual')
    scrapers = db.relationship('Scraper', back_populates='query_', lazy='select')
    results = db.relationship('Result', back_populates='query_', lazy='select') 


class Question(db.Model):
    __tablename__ = 'question'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    position = db.Column(db.Integer)
    interval = db.Column(db.Integer)
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='questions', lazy='select')
    questiontype_id = db.Column('question_type', db.Integer, db.ForeignKey('questiontype.id'))
    questiontype = db.relationship('QuestionType', back_populates='questions', lazy='select')
    answers = db.relationship('Answer', back_populates='question', lazy='select')
    options = db.relationship('Option', back_populates='question', lazy='select')
    results = db.relationship('Result', secondary=question_result, back_populates='questions', lazy='select')


class QuestionType(db.Model):
    __tablename__ = 'questiontype'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    display = db.Column(db.String)
    questions = db.relationship('Question', back_populates='questiontype', lazy='select')

class RangeStudy(db.Model):
    __tablename__ = 'range_study'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    study = db.Column(db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    range_start = db.Column(db.Integer)
    range_end = db.Column(db.Integer)


class Result(db.Model):
    __tablename__ = 'result'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    url = db.Column(db.String)
    final_url = db.Column(db.String)
    position = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    main = db.Column(db.String)
    ip = db.Column(db.String)
    origin = db.Column(db.String)
    imported = db.Column(db.Boolean)
    normalized_url = db.Column(db.String, index=True, nullable=True)

    result_type_text = db.Column(db.String(50), nullable=True)
    engine_text = db.Column(db.String(100), nullable=True)

    assignment_count = db.Column(db.Integer, default=0, nullable=True)

    indicators = db.relationship('ClassifierIndicator', back_populates='result', lazy='select', cascade="all, delete-orphan")
    classifier = db.relationship('ClassifierResult', back_populates='result', lazy='select')
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='results', lazy='select')
    scraper_id = db.Column('scraper', db.Integer, db.ForeignKey('scraper.id'), nullable=True)
    scraper = db.relationship('Scraper', back_populates='results', lazy='select')
    serp_id = db.Column('serp', db.Integer, db.ForeignKey('serp.id'))
    serp = db.relationship('Serp', back_populates='results', lazy='select')
    query_id = db.Column('query', db.Integer, db.ForeignKey('query.id'))
    query_ = db.relationship('Query', back_populates='results', lazy='select')
    answers = db.relationship('Answer', back_populates='result', lazy='select')
    questions = db.relationship('Question', secondary=question_result, back_populates='results', lazy='select')

    from sqlalchemy.ext.associationproxy import association_proxy
    source_associations = db.relationship("ResultSource", backref="result", cascade="all, delete-orphan")
    sources = association_proxy('source_associations', 'source')


class ResultSource(db.Model):
    """
    Association model mapping a parsed Result to its physical Source (HTML/screenshot),
    including processing metadata like progress and counters.
    """
    __tablename__ = 'result_source'
    result_id = db.Column('result', db.Integer, db.ForeignKey('result.id'), primary_key=True)
    source_id = db.Column('source', db.Integer, db.ForeignKey('source.id'), nullable=True)
    
    progress = db.Column(db.Integer, default=0, nullable=False)
    counter = db.Column(db.Integer, default=0, nullable=False)

    source = db.relationship("Source")

class ResultType(db.Model):
    __tablename__ = 'resulttype'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    display = db.Column(db.String)
    filter = db.Column(db.Boolean)
    selection = db.Column(db.Boolean)
    
class StudyResulttype(db.Model):
    __tablename__ = 'study_resulttype'
    __table_args__ = {'extend_existing': True}    

    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
    resulttype_id = db.Column('resulttype', db.Integer, db.ForeignKey('resulttype.id'))


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    update_datetime = db.Column(db.DateTime)
    permissions = db.Column(db.String)
    users = db.relationship('User', secondary=user_role, back_populates='roles', lazy='select')


class Scraper(db.Model):
    __tablename__ = 'scraper'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    progress = db.Column(db.Integer)
    limit = db.Column(db.Integer)
    counter = db.Column(db.Integer)
    error_code = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    type = db.Column(db.Integer)
    resulttype = db.Column(db.Integer)
    query_id = db.Column('query', db.Integer, db.ForeignKey('query.id'))
    query_ = db.relationship('Query', back_populates='scrapers', lazy='select')
    searchengine_id = db.Column('searchengine', db.Integer, db.ForeignKey('searchengine.id'))
    searchengine = db.relationship('SearchEngine', back_populates='scrapers', lazy='select')
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='scrapers', lazy='select')
    results = db.relationship('Result', back_populates='scraper', lazy='select')
    serps = db.relationship('Serp', back_populates='scraper', lazy='select')

    
class SearchEngine(db.Model):
    __tablename__ = 'searchengine'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    scrapers = db.relationship('Scraper', back_populates='searchengine', lazy='select')
    studies = db.relationship('Study', secondary=searchengine_study, back_populates='searchengines', lazy='select')


class Serp(db.Model):
    __tablename__ = 'serp'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.Integer)
    file_path = db.Column(db.String(255), nullable=True)
    progress = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    scraper_id = db.Column('scraper', db.Integer, db.ForeignKey('scraper.id'))
    scraper = db.relationship('Scraper', back_populates='serps', lazy='select')
    results = db.relationship('Result', back_populates='serp', lazy='select')
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', backref=db.backref('serps', lazy=True, cascade="all, delete-orphan"))
    assignment_count = db.Column(db.Integer, default=0, nullable=True)
    answers = db.relationship('Answer', back_populates='result_serp', lazy='select')
    result_type_text = db.Column(db.String(50), nullable=True)
    engine_text = db.Column(db.String(100), nullable=True)


class Source(db.Model):
    __tablename__ = 'source'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String)
    file_path = db.Column(db.String(255), nullable=True)
    progress = db.Column(db.Integer)
    content_type = db.Column(db.String)
    error_code = db.Column(db.String)
    status_code = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)


class Study(db.Model):
    __tablename__ = 'study'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    result_count = db.Column(db.Integer)
    status = db.Column(db.Integer)
    show_urls = db.Column(db.Boolean)
    show_ai_sources = db.Column(db.Boolean)
    task = db.Column(db.String)
    
    live_link_mode = db.Column(db.Boolean, default=True, nullable=False)

    limit_per_participant = db.Column(db.Boolean, default=False, nullable=False)
    max_results_per_participant = db.Column(db.Integer, nullable=True)
    skippable = db.Column(db.Boolean, default=True, nullable=False)
    assess_failed = db.Column(db.Boolean, default=False, nullable=True)
    completion_text = db.Column(db.Text, nullable=True)
    result_types = db.Column(db.String)
    assessable_result_types_text = db.Column(db.String, nullable=True)
    visible = db.Column(db.Boolean, default=True, nullable=False)

    assessment_result_types = db.relationship('ResultType', secondary='study_resulttype', lazy='subquery', backref=db.backref('studies', lazy=True))
    answers = db.relationship('Answer', back_populates='study', lazy='select', cascade="all, delete-orphan")
    queries = db.relationship('Query', back_populates='study', lazy='select', cascade="all, delete-orphan")
    questions = db.relationship('Question', back_populates='study', lazy='select', cascade="all, delete-orphan")
    results = db.relationship('Result', back_populates='study', lazy='select', cascade="all, delete-orphan")
    scrapers = db.relationship('Scraper', back_populates='study', lazy='select', cascade="all, delete-orphan")
    study_url_filters = db.relationship('StudyURLFilter', back_populates='study', lazy='select', cascade="all, delete-orphan")
    searchengines = db.relationship('SearchEngine', secondary=searchengine_study, back_populates='studies', lazy='select')
    users = db.relationship('User', secondary=study_user, back_populates='studies', lazy='select')
    participants = db.relationship('Participant', secondary=participant_study, back_populates='studies', lazy='select')
    classifier = db.relationship('Classifier', secondary=classifier_study, back_populates='studies', lazy='select')



class User(db.Model, UserMixin):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    password = db.Column(db.String)
    active = db.Column(db.Boolean)
    fs_uniquifier = db.Column(db.String)
    confirmed_at = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String)
    current_login_ip = db.Column(db.String)
    login_count = db.Column(db.Integer)
    tf_totp_secret = db.Column(db.String)
    tf_primary_method = db.Column(db.String)
    tf_phone_number = db.Column(db.String)
    create_datetime = db.Column(db.DateTime)
    update_datetime = db.Column(db.DateTime)
    username = db.Column(db.String)
    us_totp_secrets = db.Column(db.String)
    fs_webauthn_user_handle = db.Column(db.String)
    mf_recovery_codes = db.Column(db.String)
    us_phone_number = db.Column(db.String)
    newsletter_opt_in = db.Column(db.Boolean, default=False)
    super_admin = db.Column(db.Boolean, default=False)

    roles = db.relationship('Role', secondary=user_role, back_populates='users', lazy='select')
    studies = db.relationship('Study', secondary=study_user, back_populates='users', lazy='select')
    qs_studies = db.relationship('Qs_Study', secondary=qs_study_user, back_populates='users', lazy='select')

# ==============================================================================
# AI & CHATBOT RESULT MODELS
# ==============================================================================

class ResultAi(db.Model):
    __tablename__ = 'result_ai'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.Text)
    answer_html = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    assignment_count = db.Column(db.Integer)
    scraper_id = db.Column('scraper', db.Integer, db.ForeignKey('scraper.id'))
    scraper = db.relationship('Scraper', backref=db.backref('result_ais', lazy=True))
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', backref=db.backref('result_ais', lazy=True, cascade="all, delete-orphan"))
    query_id = db.Column('query', db.Integer, db.ForeignKey('query.id'))
    query = db.relationship('Query', backref=db.backref('result_ais', lazy=True))
    sources = db.relationship('ResultAiSource', back_populates='result_ai', lazy='select')
    result_type_text = db.Column(db.String(50), nullable=True)
    engine_text = db.Column(db.String(100), nullable=True)
    answers = db.relationship('Answer', back_populates='result_ai', lazy='select')


class ResultAiSource(db.Model):
    __tablename__ = 'result_ai_source'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    error_code = db.Column(db.String)
    job_server = db.Column(db.String)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    position = db.Column(db.Integer)
    main = db.Column(db.Text)
    final_url = db.Column(db.Text)
    ip = db.Column(db.String)
    normalized_url = db.Column(db.Text)
    progress = db.Column(db.Integer)
    counter = db.Column(db.Integer)
    result_ai_id = db.Column('result_ai', db.Integer, db.ForeignKey('result_ai.id'))
    result_ai = db.relationship('ResultAi', back_populates='sources')
    source_id = db.Column('source', db.Integer, db.ForeignKey('source.id'))
    source = db.relationship('Source', backref=db.backref('result_ai_sources', lazy=True))
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', backref=db.backref('result_ai_sources', lazy=True, cascade="all, delete-orphan"))
    scraper_id = db.Column('scraper', db.Integer, db.ForeignKey('scraper.id'))
    scraper = db.relationship('Scraper', backref=db.backref('result_ai_sources', lazy=True))
    query_id = db.Column('query', db.Integer, db.ForeignKey('query.id'))
    query = db.relationship('Query', backref=db.backref('result_ai_sources', lazy='select'))
    country_id = db.Column('country', db.Integer, db.ForeignKey('country.id'))
    country = db.relationship('Country', backref=db.backref('result_ai_sources', lazy=True))
    result_type_text = db.Column(db.String(50), nullable=True)
    engine_text = db.Column(db.String(100), nullable=True)


class ResultChatbot(db.Model):
    __tablename__ = 'result_chatbot'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.Text)
    answer_html = db.Column(db.Text)
    created_at = db.Column(db.DateTime)
    assignment_count = db.Column(db.Integer)
    scraper_id = db.Column('scraper', db.Integer, db.ForeignKey('scraper.id'))
    scraper = db.relationship('Scraper', backref=db.backref('result_chatbots', lazy=True))
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', backref=db.backref('result_chatbots', lazy=True, cascade="all, delete-orphan"))
    query_id = db.Column('query', db.Integer, db.ForeignKey('query.id'))
    query = db.relationship('Query', backref=db.backref('result_chatbots', lazy=True))
    answers = db.relationship('Answer', back_populates='result_chatbot', lazy='select')
    result_type_text = db.Column(db.String(50), nullable=True)
    engine_text = db.Column(db.String(100), nullable=True)