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

logger_query = db.Table('logger_query',
                        db.Column('logger', db.ForeignKey(
                            'logger.id'), primary_key=True),
                        db.Column('query', db.ForeignKey(
                            'query.id'), primary_key=True), extend_existing=True,
                        )

logger_result = db.Table('logger_result',
                         db.Column('logger', db.ForeignKey(
                             'logger.id'), primary_key=True),
                         db.Column('result', db.ForeignKey(
                             'result.id'), primary_key=True), extend_existing=True,
                         )

logger_scraper = db.Table('logger_scraper',
                          db.Column('logger', db.ForeignKey(
                              'logger.id'), primary_key=True),
                          db.Column('scraper', db.ForeignKey(
                              'scraper.id'), primary_key=True), extend_existing=True,
                          )

logger_searchengine = db.Table('logger_searchengine',
                               db.Column('logger', db.ForeignKey(
                                   'logger.id'), primary_key=True),
                               db.Column('searchengine', db.ForeignKey(
                                   'searchengine.id'), primary_key=True), extend_existing=True,
                               )

logger_serp = db.Table('logger_serp',
                       db.Column('logger', db.ForeignKey(
                           'logger.id'), primary_key=True),
                       db.Column('serp', db.ForeignKey(
                           'serp.id'), primary_key=True), extend_existing=True,
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

result_source = db.Table('result_source',
                         db.Column('result', db.ForeignKey('result.id')),
                         db.Column('source', db.ForeignKey('source.id')), extend_existing=True,
                         )

classifier_study = db.Table('classifier_study',
                         db.Column('classifier', db.ForeignKey('classifier.id')),
                         db.Column('study', db.ForeignKey('study.id')), extend_existing=True,
                         )


class Answer(db.Model):
    """Model for storing answers given by participants to questions."""
    __tablename__ = 'answer'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String)
    status = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    source_status_code = db.Column(db.Integer)

    participant_id = db.Column(
        'participant', db.Integer, db.ForeignKey('participant.id'))
    participant = db.relationship(
        'Participant', back_populates='answers', lazy='select')

    question_id = db.Column('question', db.Integer,
                            db.ForeignKey('question.id'))
    question = db.relationship(
        'Question', back_populates='answers', lazy='select')

    result_id = db.Column('result', db.Integer, db.ForeignKey('result.id'))
    result = db.relationship('Result', back_populates='answers', lazy='select')

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
    study = db.relationship('Study', back_populates='answers', lazy='select')


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

    result_id = db.Column('result', db.Integer, db.ForeignKey('result.id'))
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

    result_id = db.Column(db.Integer, db.ForeignKey('result.id'))
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

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
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


class Incentive(db.Model):
    """Model for storing incentives given to participants."""
    __tablename__ = 'incentive'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
    study = db.relationship(
        'Study', back_populates='incentives', lazy='select')

    participant_id = db.Column(
        'participant', db.Integer, db.ForeignKey('participant.id'))
    participant = db.relationship(
        'Participant', back_populates='incentives', lazy='select')


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


class Logger(db.Model):
    """Model for storing loggers that manage various tasks and interactions."""
    __tablename__ = 'logger'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    clicked = db.Column(db.Boolean)
    limit = db.Column(db.String)

    tasks = db.relationship('Task', back_populates='logger', lazy='select')

    queries = db.relationship(
        'Query', secondary=logger_query, back_populates='loggers', lazy='select')
    results = db.relationship(
        'Result', secondary=logger_result, back_populates='loggers', lazy='select')
    scrapers = db.relationship(
        'Scraper', secondary=logger_scraper, back_populates='loggers', lazy='select')
    searchengines = db.relationship(
        'SearchEngine', secondary=logger_searchengine, back_populates='loggers', lazy='select')
    serps = db.relationship('Serp', secondary=logger_serp,
                            back_populates='loggers', lazy='select')


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
    incentives = db.relationship(
        'Incentive', back_populates='participant', lazy='select')
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



    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
    study = db.relationship('Study', back_populates='queries', lazy='select')



    monitoring_id = db.Column('monitoring', db.Integer,
                              db.ForeignKey('monitoring.id'))
    monitoring = db.relationship(
        'Monitoring', back_populates='queries', lazy='select')

    scrapers = db.relationship(
        'Scraper', back_populates='query_', lazy='select')
    #serps = db.relationship('Serp', back_populates='query', lazy='select')
    results = db.relationship('Result', back_populates='query_', lazy='select')

    loggers = db.relationship(
        'Logger', secondary=logger_query, back_populates='queries', lazy='select')
    

    




class Question(db.Model):
    """Model for storing questions posed in studies."""
    __tablename__ = 'question'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    description = db.Column(db.String)
    position = db.Column(db.Integer)
    interval = db.Column(db.Integer)

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
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
    study = db.Column(db.Integer, db.ForeignKey('study.id'))
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

    indicators = db.relationship(
        'ClassifierIndicator', back_populates='result', uselist=False, lazy='select')

    classifier = db.relationship(
        'ClassifierResult', back_populates='result', lazy='select')

    monitoring_id = db.Column('monitoring', db.Integer,
                              db.ForeignKey('monitoring.id'))
    monitoring = db.relationship(
        'Monitoring', back_populates='results', lazy='select')

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
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
    loggers = db.relationship(
        'Logger', secondary=logger_result, back_populates='results', lazy='select')
    questions = db.relationship(
        'Question', secondary=question_result, back_populates='results', lazy='select')

    sources = db.relationship(
        'Source', secondary=result_source, back_populates='results', lazy='select')


class ResultType(db.Model):
    __tablename__ = 'resulttype'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    display = db.Column(db.String)

    monitorings = db.relationship(
        'Monitoring', back_populates='resulttype', lazy='select')
    studies = db.relationship(
        'Study', back_populates='resulttype', lazy='select')


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

    query_id = db.Column('query', db.Integer, db.ForeignKey('query.id'))
    query_ = db.relationship('Query', back_populates='scrapers', lazy='select')

    searchengine_id = db.Column(
        'searchengine', db.Integer, db.ForeignKey('searchengine.id'))
    searchengine = db.relationship(
        'SearchEngine', back_populates='scrapers', lazy='select')

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
    study = db.relationship('Study', back_populates='scrapers', lazy='select')

    results = db.relationship(
        'Result', back_populates='scraper', lazy='select')
    serps = db.relationship('Serp', back_populates='scraper', lazy='select')
    reportings = db.relationship(
        'Reporting', back_populates='scraper', lazy='select')
    loggers = db.relationship(
        'Logger', secondary=logger_scraper, back_populates='scrapers', lazy='select')
    
class SearchEngine(db.Model):
    """Model for storing search engines used in studies."""
    __tablename__ = 'searchengine'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    module = db.Column(db.String)
    test = db.Column(db.Integer)

    scrapers = db.relationship(
        'Scraper', back_populates='searchengine', lazy='select')
    countries = db.relationship(
        'Country', back_populates='searchengine', lazy='select')
    loggers = db.relationship('Logger', secondary=logger_searchengine,
                              back_populates='searchengines', lazy='select')
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

    loggers = db.relationship(
        'Logger', secondary=logger_serp, back_populates='serps', lazy='select')

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

    results = db.relationship(
        'Result', secondary=result_source, back_populates='sources', lazy='select')

    evaluation = db.relationship(
        'Evaluation', back_populates='source', uselist=False, lazy='select')


class Statistic(db.Model):
    """Model for storing statistics."""
    __tablename__ = 'statistic'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    value = db.Column(db.String)

    study_id = db.Column('study', db.Integer, db.ForeignKey('study.id'))
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
    task = db.Column(db.String)

    studytype_id = db.Column('studytype', db.Integer,
                             db.ForeignKey('studytype.id'))
    studytype = db.relationship(
        'StudyType', back_populates='studies', lazy='select')

    resulttype_id = db.Column('resulttype', db.Integer,
                              db.ForeignKey('resulttype.id'))
    resulttype = db.relationship(
        'ResultType', back_populates='studies', lazy='select')

    answers = db.relationship('Answer', back_populates='study', lazy='select')
    experiments = db.relationship(
        'Experiment', back_populates='study', lazy='select')
    incentives = db.relationship(
        'Incentive', back_populates='study', lazy='select')
    statistics = db.relationship(
        'Statistic', back_populates='study', lazy='select')
    queries = db.relationship('Query', back_populates='study', lazy='select')
    questions = db.relationship(
        'Question', back_populates='study', lazy='select')
    results = db.relationship('Result', back_populates='study', lazy='select')
    scrapers = db.relationship(
        'Scraper', back_populates='study', lazy='select')
    languages = db.relationship(
        'Language', secondary=language_study, back_populates='studies', lazy='select')
    searchengines = db.relationship(
        'SearchEngine', secondary=searchengine_study, back_populates='studies', lazy='select')
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

    studies = db.relationship(
        'Study', back_populates='studytype', lazy='select')


class Task(db.Model):
    """Model for storing tasks associated with loggers."""
    __tablename__ = 'task'
    __table_args__ = {'extend_existing': True}


    id = db.Column(db.Integer, primary_key=True)

    logger_id = db.Column('logger', db.Integer, db.ForeignKey('logger.id'))
    logger = db.relationship('Logger', back_populates='tasks', lazy='select')


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



