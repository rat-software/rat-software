from flask_wtf import FlaskForm, RecaptchaField
from wtforms import (StringField, SubmitField, SelectField, TextAreaField,
                     BooleanField, SelectMultipleField, widgets, FieldList,
                     FormField, RadioField, IntegerField, DecimalField,
                     IntegerRangeField, PasswordField, EmailField,
                     HiddenField, DateField, TimeField)
from wtforms.validators import InputRequired, Optional, NumberRange
from flask_wtf.file import FileField
from flask_security.forms import RegisterForm, SendConfirmationForm, ForgotPasswordForm

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

# NEU: Erweitertes Registrierungsformular mit reCAPTCHA
class ExtendedRegisterForm(RegisterForm):
    recaptcha = RecaptchaField()

# NEU: Erweitertes Bestätigungsformular mit reCAPTCHA
class ExtendedSendConfirmationForm(SendConfirmationForm):
    recaptcha = RecaptchaField()

# NEU: Erweitertes "Passwort vergessen"-Formular mit reCAPTCHA
class ExtendedForgotPasswordForm(ForgotPasswordForm):
    recaptcha = RecaptchaField()


class RangeForm(FlaskForm):
    start_range = IntegerField("Start Value", validators=[NumberRange(min=1, message="Value must be positive.")])
    end_range = IntegerField("End Value", validators=[NumberRange(min=1, message="Value must be positive.")])

class StudyForm(FlaskForm):
    id = HiddenField("Study ID", default=0)
    name = StringField("Study name", [InputRequired("Input required.")])
    description = TextAreaField("Description [optional]")
    type = SelectField("Study type", coerce=int)
    imported = BooleanField("Import own search results", default=False)
    imported_data = FileField("Add own search results (csv)")
    search_engines = MultiCheckboxField("Select search engines", coerce=int)
    classifiers = MultiCheckboxField("", coerce=int)
    show_urls = BooleanField("", default=False)

    show_ai_sources = BooleanField('Show sources for the AI overviews in the Assessment Interface [optional]')


    queries = TextAreaField("Queries (use new line for each query)")
    
    assessment_result_types = MultiCheckboxField(
        'Result Types for Assessment', 
        coerce=int
    )

    query_list = FileField("List of queries (csv)")
    task = StringField("Search Task (use *** as a placeholder for the query)", default="In the following, you see the results for the query ***. Please assess the results using the questions below.")
    result_count = IntegerField("Number of search results to collect", default=10, validators=[NumberRange(min=1, max=10000, message="The number of results can be between 1 and 10000.")])
    ranges = FieldList(FormField(RangeForm), min_entries=1, max_entries=100, label="Result Ranges")
    start_date = DateField("Start Date", format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField("End Date", format='%Y-%m-%d', validators=[Optional()])
    start_time = TimeField("Start Time", format='%H:%M', validators=[Optional()])
    end_time = TimeField("End Time", format='%H:%M', validators=[Optional()])
    repeat_frequency = SelectField(
        "Repeat",
        choices=[("none", "Does not repeat"), ("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly"), ("custom", "Custom")]
    )
    all_day = BooleanField("All day", default=False)
    repeat_interval = IntegerField("Repeat every", validators=[Optional()], default=1)
    repeat_unit = SelectField("Repeat unit", choices=[("day", "day(s)"), ("week", "week(s)"), ("month", "month(s)")], validators=[Optional()])
    occurrences = IntegerField("Occurrences", validators=[NumberRange(min=1)])
    limit_per_participant = BooleanField('Limit number of results to assess per participant [optional]')
    max_results_per_participant = IntegerField(
        'Maximum results per participant',
        default=20,
        validators=[Optional()]
    )
    url_filter_include = TextAreaField("Add the list of URLs that you want to include in your result set for the Assessment Interface (use a new line for each URL) [optional]", validators=[Optional()], render_kw={"placeholder": "e.g. example.com"})
    url_filter_exclude = TextAreaField("Add the list of URLs that you want to exclude from your result set for the Assessment Interface (use a new line for each URL) [optional]", validators=[Optional()], render_kw={"placeholder": "e.g. example.com"})    
    url_list = FileField("List of URLs (csv,xlsx)")
    submit = SubmitField("Create study")



class MonitoringForm(FlaskForm):
    name = StringField("Monitoring name")
    description = TextAreaField("Monitoring description")
    queries = TextAreaField("Queries (use new line for each query)")
    countries = MultiCheckboxField("Select countries", coerce=int)
    result_count = IntegerField("Number of results to collect")
    result_type = SelectField("Select result types", choices=[(2, "Snippets")], coerce=int)
    interval_frequency = SelectField("Frequency", choices=[(1, "once"), (2, "twice")])
    interval_mode = SelectField("Mode",
                                choices=[(1, "daily"), (2, "weekly"), (3, "monthly")],
                                coerce=int)
    submit = SubmitField("Create monitoring")

class ConfirmationForm(FlaskForm):
    data = HiddenField("Data")
    submit = SubmitField("Confirm")

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
    """
    Ein Formular, das alle Schritte des Query Sampler Wizards abdeckt.
    JETZT MIT EINZELAUSWAHL.
    """
    # Schritt 1: Study Details
    name = StringField("Study Name", [InputRequired("Ein Name ist erforderlich.")])
    description = TextAreaField("Description (optional)")

    # Schritt 2: Targeting Options - GEÄNDERT ZU SelectField
    geotargets = SelectField("Country",
                                coerce=int,
                                validators=[InputRequired("Wähle ein Land aus.")])
    languages = SelectField("Language",
                                   coerce=int,
                                   validators=[InputRequired("Wähle eine Sprache aus.")])

    # Schritt 3: Seed Keywords
    seed_keywords = TextAreaField("Seed Keywords",
                                  [InputRequired("Gib mindestens ein Seed-Keyword ein.")],
                                  render_kw={"placeholder": "Ein Keyword pro Zeile..."})

    # Verstecktes Feld für den Bestätigungsschritt
    submit = SubmitField("Create Study")

class EditQsStudyForm(FlaskForm):
    """
    Formular zum Bearbeiten einer bestehenden Query Sampler Studie.
    """
    name = StringField("Study Name", [InputRequired("A name is required.")])
    description = TextAreaField("Description (optional)")
    new_keywords = TextAreaField("Add New Seed Keywords",
                                 render_kw={"placeholder": "One keyword per line..."})
    submit = SubmitField("Save Changes")