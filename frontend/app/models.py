from app import db
from flask_security import UserMixin, RoleMixin

# Define association tables for many-to-many relationships

country_monitoring = db.Table('country_monitoring',
                              db.Column('country', db.ForeignKey(
                                  'country.id'), primary_key=True),
                              db.Column('monitoring', db.ForeignKey(
                                  'monitoring.id'), primary_key=True), extend_existing=True,
                              )

language_study = db.Table('language_study',
                          db.Column('language', db.ForeignKey(
                              'language.id'), primary_key=True),
                          db.Column('study', db.ForeignKey(
                              'study.id'), primary_key=True), extend_existing=True,
                          )



participant_study = db.Table('participant_study',
                             db.Column('participant', db.ForeignKey(
                                 'participant.id'), primary_key=True),
                             db.Column('study', db.ForeignKey(
                                 'study.id'), primary_key=True), extend_existing=True,
                             )

question_result = db.Table('question_result',
                           db.Column('question', db.ForeignKey(
                               'question.id'), primary_key=True),
                           db.Column('result', db.ForeignKey(
                               'result.id'), primary_key=True), extend_existing=True,
                           )

searchengine_study = db.Table('searchengine_study',
                              db.Column('searchengine', db.ForeignKey(
                                  'searchengine.id'), primary_key=True),
                              db.Column('study', db.ForeignKey(
                                  'study.id'), primary_key=True), extend_existing=True,
                              )

study_user = db.Table('study_user',
                      db.Column('study', db.ForeignKey(
                          'study.id'), primary_key=True),
                      db.Column('user', db.ForeignKey(
                          'user.id'), primary_key=True), extend_existing=True,
                      )

user_role = db.Table('user_role',
                     db.Column('user', db.ForeignKey(
                         'user.id'), primary_key=True),
                     db.Column('role', db.ForeignKey(
                         'role.id'), primary_key=True), extend_existing=True,
                     )



classifier_study = db.Table('classifier_study',
                         db.Column('classifier', db.ForeignKey('classifier.id')),
                         db.Column('study', db.ForeignKey('study.id')), extend_existing=True,
                         )

qs_study_user = db.Table('qs_study_user',
    db.Column('qs_study', db.Integer, db.ForeignKey('qs_study.id'), primary_key=True),
    db.Column('user', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    extend_existing=True
)


class ResultSource(db.Model):
    __tablename__ = 'result_source'
    # Wichtig: Die Spaltennamen 'result' und 'source' entsprechen deiner Datenbank
    result_id = db.Column('result', db.Integer, db.ForeignKey('result.id'), primary_key=True)
    source_id = db.Column('source', db.Integer, db.ForeignKey('source.id'), primary_key=True)
    
    # Hier sind die Spalten, die du für deine Logik brauchst:
    progress = db.Column(db.Integer, default=0, nullable=False)
    counter = db.Column(db.Integer, default=0, nullable=False)

    # Beziehung zum Source-Modell
    source = db.relationship("Source")

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

class Qs_Study(db.Model):
    __tablename__ = 'qs_study'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    status = db.Column(db.Integer)
    users = db.relationship('User', secondary=qs_study_user, back_populates='qs_studies', lazy='select')
    description = db.Column(db.String, nullable=True)  # <-- DIESE ZEILE HINZUFÜGEN





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

    participant_id = db.Column(
        'participant', db.Integer, db.ForeignKey('participant.id'))
    participant = db.relationship(
        'Participant', back_populates='answers', lazy='select')

    question_id = db.Column('question', db.Integer,
                            db.ForeignKey('question.id'))
    question = db.relationship(
        'Question', back_populates='answers', lazy='select')


    result_id = db.Column('result', db.Integer, db.ForeignKey('result.id'), nullable=True)
    result = db.relationship('Result', back_populates='answers', lazy='select')

    result_ai_id = db.Column('result_ai', db.Integer, db.ForeignKey('result_ai.id'), nullable=True)
    result_ai = db.relationship('ResultAi', back_populates='answers', lazy='select')

    result_chatbot_id = db.Column('result_chatbot', db.Integer, db.ForeignKey('result_chatbot.id'), nullable=True)
    result_chatbot = db.relationship('ResultChatbot', back_populates='answers', lazy='select')

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='answers', lazy='select')

    __table_args__ = (
        db.Index('idx_answer_lookup', 'participant', 'study', 'status'),
        {'extend_existing': True}
    )


class ClassifierResult(db.Model):
    """Model for storing the results produced by classifiers."""
    __tablename__ = 'classifier_result'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)

    classifier_id = db.Column("classifier", db.Integer, db.ForeignKey('classifier.id'))
    result_id = db.Column("result", db.Integer, db.ForeignKey('result.id'))

    value = db.Column('value', db.String)
    created_at = db.Column(db.DateTime)

    classifier = db.relationship("Classifier", back_populates="results")
    result = db.relationship("Result", back_populates="classifier")



class Classifier(db.Model):
    """Model for storing classifiers used in studies."""
    __tablename__ = 'classifier'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column('name', db.String)
    display_name = db.Column('display_name', db.String)
    display = db.Column(db.Boolean)

    indicators = db.relationship(
        'ClassifierIndicator', back_populates='classifier', uselist=False, lazy='select')

    results = db.relationship(
        'ClassifierResult', back_populates='classifier', lazy='select')

    studies = db.relationship(
        'Study', secondary=classifier_study, back_populates='classifier', lazy='select')


class ClassifierIndicator(db.Model):
    """Model for storing indicators used by classifiers."""
    __tablename__ = 'classifier_indicator'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    indicator = db.Column('indicator', db.String)
    value = db.Column('value', db.String)
    created_at = db.Column(db.DateTime)

    # KORRIGIERT: Expliziter Spaltenname 'result' und Best Practices
    result_id = db.Column('result', db.Integer, db.ForeignKey('result.id', ondelete='CASCADE'), index=True)
    result = db.relationship(
        'Result', back_populates='indicators', lazy='select')

    classifier_id = db.Column('classifier', db.Integer, db.ForeignKey('classifier.id'))
    classifier = db.relationship(
        'Classifier', back_populates='indicators', lazy='select')


class Content(db.Model):
    """Model for storing content related to results."""
    __tablename__ = 'content'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String)

    # KORRIGIERT: Expliziter Spaltenname 'result'
    result_id = db.Column('result', db.Integer, db.ForeignKey('result.id', ondelete='CASCADE'), index=True)
    result = db.relationship(
        'Result', back_populates='contents', lazy='select')


class Country(db.Model):
    """Model for storing countries involved in various studies."""
    __tablename__ = 'country'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    code = db.Column(db.String)

    searchengine_id = db.Column(
        'searchengine', db.Integer, db.ForeignKey('searchengine.id'))
    searchengine = db.relationship(
        'SearchEngine', back_populates='countries', lazy='select')

    language_id = db.Column('language', db.Integer,
                            db.ForeignKey('language.id'))
    language = db.relationship(
        'Language', back_populates='countries', lazy='select')

    monitorings = db.relationship(
        'Monitoring', secondary=country_monitoring, back_populates='countries', lazy='select')

class Provider(db.Model):
    """Model for storing providers involved in various studies."""
    __tablename__ = 'provider'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    searchengine_id = db.Column(
        'searchengine', db.Integer, db.ForeignKey('searchengine.id'))
    searchengine = db.relationship(
        'SearchEngine', back_populates='providers', lazy='select')


class Evaluation(db.Model):
    """Model for storing evaluations of sources."""
    __tablename__ = 'evaluation'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer)
    comment = db.Column(db.String)

    source_id = db.Column('source', db.Integer, db.ForeignKey('source.id'))
    source = db.relationship(
        'Source', back_populates='evaluation', lazy='select')


class Experiment(db.Model):
    """Model for storing experiments conducted within studies."""
    __tablename__ = 'experiment'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship(
        'Study', back_populates='experiments', lazy='select')


class Group(db.Model):
    """Model for storing participant groups."""
    __tablename__ = 'group'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)

    participants = db.relationship(
        'Participant', back_populates='group', lazy='select')


class StudyURLFilter(db.Model):
    __tablename__ = 'study_url_filter'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship(
        'Study', back_populates='study_url_filters', lazy='select'   
    )

    url = db.Column(db.String)
    include = db.Column(db.Boolean)
    exclude = db.Column(db.Boolean)



class Language(db.Model):
    """Model for storing languages used in studies."""
    __tablename__ = 'language'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    code = db.Column(db.String)

    countries = db.relationship(
        'Country', back_populates='language', lazy='select')
    studies = db.relationship(
        'Study', secondary=language_study, back_populates='languages', lazy='select')





class Monitoring(db.Model):
    """Model for storing monitoring processes."""
    __tablename__ = 'monitoring'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    result_count = db.Column(db.Integer)
    interval_mode = db.Column(db.Integer)
    interval_frequency = db.Column(db.Integer)

    resulttype_id = db.Column('resulttype', db.Integer,
                              db.ForeignKey('resulttype.id'))
    resulttype = db.relationship(
        'ResultType', back_populates='monitorings', lazy='select')

    queries = db.relationship(
        'Query', back_populates='monitoring', lazy='select')
    serps = db.relationship('Serp', back_populates='monitoring', lazy='select')
    results = db.relationship(
        'Result', back_populates='monitoring', lazy='select')
    countries = db.relationship(
        'Country', secondary=country_monitoring, back_populates='monitorings', lazy='select')


class Option(db.Model):
    """Model for storing options information for questions."""
    __tablename__ = 'option'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String)
    label = db.Column(db.String)
    position = db.Column(db.Integer)

    question_id = db.Column('question', db.Integer,
                            db.ForeignKey('question.id'))
    question = db.relationship(
        'Question', back_populates='options', lazy='select')


class Participant(db.Model):
    """Model for storing participant information."""
    __tablename__ = 'participant'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    password = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    group_id = db.Column('group', db.Integer, db.ForeignKey('group.id'))
    group = db.relationship(
        'Group', back_populates='participants', lazy='select')

    answers = db.relationship(
        'Answer', back_populates='participant', lazy='select')

    studies = db.relationship(
        'Study', secondary=participant_study, back_populates='participants', lazy='select')


class Query(db.Model):
    """Model for storing queries related to results."""
    __tablename__ = 'query'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String)
    description = db.Column(db.String)
    limit = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)



    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='queries', lazy='select')



    monitoring_id = db.Column('monitoring', db.Integer,
                              db.ForeignKey('monitoring.id'))
    monitoring = db.relationship(
        'Monitoring', back_populates='queries', lazy='select')

    scrapers = db.relationship(
        'Scraper', back_populates='query_', lazy='select')
    #serps = db.relationship('Serp', back_populates='query', lazy='select')
    results = db.relationship('Result', back_populates='query_', lazy='select')

    
    




class Question(db.Model):
    """Model for storing questions posed in studies."""
    __tablename__ = 'question'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    position = db.Column(db.Integer)
    interval = db.Column(db.Integer)

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='questions', lazy='select')

    questiontype_id = db.Column(
        'question_type', db.Integer, db.ForeignKey('questiontype.id'))
    questiontype = db.relationship(
        'QuestionType', back_populates='questions', lazy='select')

    questiontemplate_id = db.Column(
        'question_template', db.Integer, db.ForeignKey('questiontemplate.id'))
    questiontemplate = db.relationship(
        'QuestionTemplate', back_populates='questions', lazy='select')

    answers = db.relationship(
        'Answer', back_populates='question', lazy='select')
    options = db.relationship(
        'Option', back_populates='question', lazy='select')
    results = db.relationship(
        'Result', secondary=question_result, back_populates='questions', lazy='select')


class QuestionTemplate(db.Model):
    __tablename__ = 'questiontemplate'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)

    questions = db.relationship(
        'Question', back_populates='questiontemplate', lazy='select')


class QuestionType(db.Model):
    __tablename__ = 'questiontype'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    display = db.Column(db.String)

    questions = db.relationship(
        'Question', back_populates='questiontype', lazy='select')

class RangeStudy(db.Model):
    __tablename__ = 'range_study'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    study = db.Column(db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    range_start = db.Column(db.Integer)
    range_end = db.Column(db.Integer)

class Reporting(db.Model):
    __tablename__ = 'reporting'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    result_count = db.Column(db.Integer)
    missing_count = db.Column(db.Integer)
    duplicate_count = db.Column(db.Integer)
    exit_condition = db.Column(db.String)
    duration = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)

    scraper_id = db.Column('scraper', db.Integer, db.ForeignKey('scraper.id'))
    scraper = db.relationship(
        'Scraper', back_populates='reportings', lazy='select')


class Result(db.Model):
    """Model for storing results from various studies."""
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

    assignment_count = db.Column(db.Integer, default=0, nullable=True)

    indicators = db.relationship(
        'ClassifierIndicator', back_populates='result', lazy='select', cascade="all, delete-orphan")
    
    contents = db.relationship(
            'Content', back_populates='result', lazy='select', cascade="all, delete-orphan")

    classifier = db.relationship(
        'ClassifierResult', back_populates='result', lazy='select')

    monitoring_id = db.Column('monitoring', db.Integer,
                              db.ForeignKey('monitoring.id'))
    monitoring = db.relationship(
        'Monitoring', back_populates='results', lazy='select')

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='results', lazy='select')

    scraper_id = db.Column('scraper', db.Integer, db.ForeignKey('scraper.id'))
    scraper = db.relationship(
        'Scraper', back_populates='results', lazy='select')

    serp_id = db.Column('serp', db.Integer, db.ForeignKey('serp.id'))
    serp = db.relationship('Serp', back_populates='results', lazy='select')

    query_id = db.Column('query', db.Integer, db.ForeignKey('query.id'))
    query_ = db.relationship('Query', back_populates='results', lazy='select')

    answers = db.relationship('Answer', back_populates='result', lazy='select')
    contents = db.relationship(
        'Content', back_populates='result', lazy='select')

    questions = db.relationship(
        'Question', secondary=question_result, back_populates='results', lazy='select')

    from sqlalchemy.ext.associationproxy import association_proxy

    # Ersetze die alte "sources"-Zeile hiermit:
    source_associations = db.relationship("ResultSource", backref="result", cascade="all, delete-orphan")
    sources = association_proxy('source_associations', 'source')



class ResultType(db.Model):
    __tablename__ = 'resulttype'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    display = db.Column(db.String)
    filter = db.Column(db.Boolean)
    selection = db.Column(db.Boolean)

    monitorings = db.relationship(
        'Monitoring', back_populates='resulttype', lazy='select')
    
class StudyResulttype(db.Model):
    __tablename__ = 'study_resulttype'
    __table_args__ = {'extend_existing': True}    

    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
    resulttype_id = db.Column('resulttype', db.Integer, db.ForeignKey('resulttype.id'))


class Role(db.Model, RoleMixin):
    """Model for storing user roles."""
    __tablename__ = 'role'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    update_datetime = db.Column(db.DateTime)
    permissions = db.Column(db.String)

    users = db.relationship('User', secondary=user_role,
                            back_populates='roles', lazy='select')


class Scraper(db.Model):
    """Model for storing scraper jobs related to queries and search engines."""
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

    searchengine_id = db.Column(
        'searchengine', db.Integer, db.ForeignKey('searchengine.id'))
    searchengine = db.relationship(
        'SearchEngine', back_populates='scrapers', lazy='select')

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship('Study', back_populates='scrapers', lazy='select')

    results = db.relationship(
        'Result', back_populates='scraper', lazy='select')
    serps = db.relationship('Serp', back_populates='scraper', lazy='select')
    reportings = db.relationship(
        'Reporting', back_populates='scraper', lazy='select')

    
class SearchEngine(db.Model):
    """Model for storing search engines used in studies."""
    __tablename__ = 'searchengine'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    module = db.Column(db.String)
    test = db.Column(db.Integer)
    resulttype = db.Column(db.Integer)
    country = db.Column(db.Integer)
    provider = db.Column(db.Integer)

    scrapers = db.relationship(
        'Scraper', back_populates='searchengine', lazy='select')
    countries = db.relationship(
        'Country', back_populates='searchengine', lazy='select')
    
    providers = db.relationship(
        'Provider', back_populates='searchengine', lazy='select')

    studies = db.relationship(
        'Study', secondary=searchengine_study, back_populates='searchengines', lazy='select')


class Serp(db.Model):
    """Model for storing SERPs (Search Engine Results Pages)."""
    __tablename__ = 'serp'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.Integer)
    code = db.Column(db.LargeBinary)
    img = db.Column(db.LargeBinary)
    progress = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)

    scraper_id = db.Column('scraper', db.Integer, db.ForeignKey('scraper.id'))
    scraper = db.relationship('Scraper', back_populates='serps', lazy='select')



    monitoring_id = db.Column('monitoring', db.Integer,
                              db.ForeignKey('monitoring.id'))
    monitoring = db.relationship(
        'Monitoring', back_populates='serps', lazy='select')

    #query_id = db.Column('query', db.Integer, db.ForeignKey('query.id'))
    #query = db.relationship('Query', back_populates='serps', lazy='select')

    results = db.relationship('Result', back_populates='serp', lazy='select')


class Source(db.Model):
    """Model for storing sources used in studies."""
    __tablename__ = 'source'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.LargeBinary)
    bin = db.Column(db.LargeBinary)
    url = db.Column(db.String)
    progress = db.Column(db.Integer)
    content_type = db.Column(db.String)
    error_code = db.Column(db.String)
    status_code = db.Column(db.Integer)
    #final_url = db.Column(db.String)
    created_at = db.Column(db.DateTime)



    evaluation = db.relationship(
        'Evaluation', back_populates='source', uselist=False, lazy='select')


class Statistic(db.Model):
    """Model for storing statistics."""
    __tablename__ = 'statistic'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    value = db.Column(db.String)

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id', ondelete='CASCADE'), index=True)
    study = db.relationship(
        'Study', back_populates='statistics', lazy='select')


class Study(db.Model):
    """Model for storing studies."""
    __tablename__ = 'study'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    imported = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    result_count = db.Column(db.Integer)
    status = db.Column(db.Integer)
    show_urls = db.Column(db.Boolean)
    show_ai_sources = db.Column(db.Boolean)
    task = db.Column(db.String)

    limit_per_participant = db.Column(db.Boolean, default=False, nullable=False)
    max_results_per_participant = db.Column(db.Integer, nullable=True)

    skippable = db.Column(db.Boolean, default=True, nullable=False)

    completion_text = db.Column(db.Text, nullable=True)

    result_types = db.Column(db.String)

    studytype_id = db.Column('studytype', db.Integer,
                             db.ForeignKey('studytype.id'))
    studytype = db.relationship(
        'StudyType', back_populates='studies', lazy='select')

    assessment_result_types = db.relationship(
        'ResultType', 
        secondary='study_resulttype', 
        lazy='subquery',
        backref=db.backref('studies', lazy=True)
    )

    answers = db.relationship('Answer', back_populates='study', lazy='select', cascade="all, delete-orphan")
    experiments = db.relationship(
        'Experiment', back_populates='study', lazy='select', cascade="all, delete-orphan")

    statistics = db.relationship(
        'Statistic', back_populates='study', lazy='select', cascade="all, delete-orphan")
    queries = db.relationship('Query', back_populates='study', lazy='select', cascade="all, delete-orphan")
    questions = db.relationship(
        'Question', back_populates='study', lazy='select', cascade="all, delete-orphan")
    results = db.relationship('Result', back_populates='study', lazy='select', cascade="all, delete-orphan")
    scrapers = db.relationship(
        'Scraper', back_populates='study', lazy='select', cascade="all, delete-orphan")
    study_url_filters = db.relationship(
        'StudyURLFilter', back_populates='study', lazy='select', cascade="all, delete-orphan")
    
    languages = db.relationship(
        'Language', secondary=language_study, back_populates='studies', lazy='select')
    
    searchengines = db.relationship(
        'SearchEngine', 
        secondary=searchengine_study, 
        back_populates='studies',  # This should point to the 'studies' attribute on SearchEngine
        lazy='select'
    )

    users = db.relationship('User', secondary=study_user,
                            back_populates='studies', lazy='select')
    participants = db.relationship(
        'Participant', secondary=participant_study, back_populates='studies', lazy='select')
    classifier = db.relationship(
        'Classifier', secondary=classifier_study, back_populates='studies', lazy='select')


class StudyType(db.Model):
    """Model for storing study types."""
    __tablename__ = 'studytype'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)

    studies = db.relationship(
        'Study', back_populates='studytype', lazy='select')


class Task(db.Model):
    """Model for storing tasks associated with loggers."""
    __tablename__ = 'task'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)




class User(db.Model, UserMixin):
    """Model for storing users."""
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

    roles = db.relationship('Role', secondary=user_role,
                            back_populates='users', lazy='select')
    studies = db.relationship(
        'Study', secondary=study_user, back_populates='users', lazy='select')
    
    qs_studies = db.relationship('Qs_Study', secondary=qs_study_user, back_populates='users', lazy='select')




class ResultAi(db.Model):
    """Model for storing AI-generated answers."""
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

    answers = db.relationship('Answer', back_populates='result_ai', lazy='select')



class ResultAiSource(db.Model):
    """Model for storing the sources of AI-generated answers."""
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


class ResultChatbot(db.Model):
    """Model for storing AI-generated answers from Chatbots."""
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