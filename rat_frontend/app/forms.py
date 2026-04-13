from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (StringField, SubmitField, SelectField, TextAreaField,
                     BooleanField, SelectMultipleField, widgets, FieldList,
                     FormField, RadioField, IntegerField, DecimalField,
                     IntegerRangeField, PasswordField, EmailField,
                     HiddenField, DateField, TimeField)
from wtforms.validators import InputRequired, Optional, NumberRange, URL
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_security.forms import RegisterForm, SendConfirmationForm, ForgotPasswordForm

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class ExtendedRegisterForm(RegisterForm):
    recaptcha = RecaptchaField()

class ExtendedSendConfirmationForm(SendConfirmationForm):
    recaptcha = RecaptchaField()

class ExtendedForgotPasswordForm(ForgotPasswordForm):
    recaptcha = RecaptchaField()

class RangeForm(FlaskForm):
    start_range = IntegerField("Start", validators=[NumberRange(min=1)])
    end_range = IntegerField("End", validators=[NumberRange(min=1)])

class StudyForm(FlaskForm):
    id = HiddenField("Study ID", default=0)
    name = StringField("Study name", [InputRequired("Input required.")])
    description = TextAreaField("Description [optional]")
    submit = SubmitField("Create study")

class UploadResultsForm(FlaskForm):
    results_file = FileField("Upload Scraped Data", 
                             validators=[
                                 InputRequired(), 
                                 FileAllowed(['zip', 'json', 'csv'], 'ZIP, JSON or CSV files only!')
                             ])
    submit_upload = SubmitField("Upload Data")

class ConfirmUploadForm(FlaskForm):
    filename = HiddenField("Filename")
    submit_confirm = SubmitField("Confirm Import")

class StudySettingsForm(FlaskForm):
    # Assessment Limits
    result_count = IntegerField("Top results to assess per query", default=10, validators=[NumberRange(min=1)])
    
    assessment_result_types = MultiCheckboxField('Result Types for Assessment') 
    
    show_urls = BooleanField("Show URLs in Assessment Interface")
    show_ai_sources = BooleanField("Show sources for AI overviews")
    assess_failed = BooleanField("Allow assessment of failed/missing sources (Show URL only)")
    
    live_link_mode = BooleanField("Live Link Mode", default=True)
    
    # Participant Limits
    limit_per_participant = BooleanField('Limit workload per participant')
    max_results_per_participant = IntegerField('Max results per participant', validators=[Optional(), NumberRange(min=1)])
    
    # Ranges
    ranges = FieldList(FormField(RangeForm), min_entries=0, max_entries=50, label="Result Ranges")
    
    # Classifiers
    classifiers = MultiCheckboxField("Select Classifiers", coerce=int)
    
    submit_settings = SubmitField("Save Configuration")

class AnswerOptions(FlaskForm):
    value = StringField("Value")
    label = StringField("Label")

class RangeOptions(FlaskForm):
    start = IntegerField("Starting Value", default=0)
    stop = IntegerField("End Value", default=100)
    step = DecimalField("Steps", default=1)
    start_text = StringField("Start Text")
    stop_text = StringField("Stop Text")

class QuestionForm(FlaskForm):
    q_type = SelectField("Question type")
    text = StringField("Question")
    position = IntegerField("Question number")
    options = FieldList(FormField(AnswerOptions), min_entries=2, label="Answer Options")
    ranges = FieldList(FormField(RangeOptions), min_entries=1, label="Range Options")
    submit = SubmitField("Create question")

class ImportQuestionsForm(FlaskForm):
    file = FileField('Questionnaire JSON File', validators=[
        FileRequired(),
        FileAllowed(['json'], 'JSON files only!')
    ])
    submit = SubmitField('Import Questions')

class AnswerForm(FlaskForm):
    short_text = StringField("Answer")
    long_text = TextAreaField("Answer")
    true_false = RadioField("Answer")
    likert_scale = RadioField("Answer")
    multiple_choice = SelectMultipleField("Answer")
    scale_number = IntegerRangeField("Answer")
    submit = SubmitField("Submit")

class EvaluationForm(FlaskForm):
    status = RadioField("Status", choices=[(1, "OK"), (0, "Not OK")], coerce=int)
    comment = TextAreaField("Comment")
    submit = SubmitField("Submit")

class JoinForm(FlaskForm):
    new = SubmitField("New")
    returning = SubmitField("Returning")

class ParticipantLogInForm(FlaskForm):
    username = StringField("Username")
    password = PasswordField("Code")
    submit = SubmitField("Log in")

class ExportForm(FlaskForm):
    tables = RadioField("Select data to export:")
    submit = SubmitField("Generate Excel")

class ContactForm(FlaskForm):
    name = StringField("Name")
    email = EmailField("E-Mail")
    message = TextAreaField("Message")
    recaptcha = RecaptchaField()
    submit = SubmitField("Send")

class KeywordsForm(FlaskForm):
    keywords = TextAreaField("Keywords", [InputRequired("Please enter keywords.")])
    language_criterion = SelectField("Language", coerce=int)
    region_criterion = SelectField("Region", coerce=int)
    submit = SubmitField("Save")

class QuerySamplerWizardForm(FlaskForm):
    name = StringField("Study Name", [InputRequired("A name is required.")])
    description = TextAreaField("Description (optional)")
    geotargets = SelectField("Country", coerce=int, validators=[InputRequired("Select a country.")])
    languages = SelectField("Language", coerce=int, validators=[InputRequired("Select a language.")])
    seed_keywords = TextAreaField("Seed Keywords", [InputRequired("Enter at least one seed keyword.")], render_kw={"placeholder": "One keyword per line..."})
    query_list = FileField('List of queries (csv)')
    submit = SubmitField("Create Study")
    
class EditQsStudyForm(FlaskForm):
    name = StringField("Study Name", [InputRequired("A name is required.")])
    description = TextAreaField("Description (optional)")
    new_keywords = TextAreaField("Add New Seed Keywords", render_kw={"placeholder": "One keyword per line..."})
    submit = SubmitField("Save Changes")

class MonitoringForm(FlaskForm):
    name = StringField("Monitoring name")
    description = TextAreaField("Monitoring description")
    queries = TextAreaField("Queries (use new line for each query)")
    countries = MultiCheckboxField("Select countries", coerce=int)
    result_count = IntegerField("Number of results to collect")
    result_type = SelectField("Select result types", choices=[(2, "Snippets")], coerce=int)
    interval_frequency = SelectField("Frequency", choices=[(1, "once"), (2, "twice")])
    interval_mode = SelectField("Mode", choices=[(1, "daily"), (2, "weekly"), (3, "monthly")], coerce=int)
    submit = SubmitField("Create monitoring")

class ConfirmationForm(FlaskForm):
    data = HiddenField("Data")
    submit = SubmitField("Confirm")