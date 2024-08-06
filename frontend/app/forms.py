from flask_wtf import FlaskForm
from wtforms import (StringField, SubmitField, SelectField, TextAreaField, 
                     BooleanField, SelectMultipleField, widgets, FieldList, 
                     FormField, RadioField, IntegerField, DecimalField, 
                     IntegerRangeField, PasswordField, EmailField, 
                     validators, HiddenField)
from flask_wtf.file import FileField


class MultiCheckboxField(SelectMultipleField):
    """
    A custom field for multiple checkbox inputs.

    Inherits from SelectMultipleField and uses a ListWidget with CheckBoxInput.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class StudyForm(FlaskForm):
    """
    Form for creating or editing a study.

    Fields include study details, file uploads, search engines, classifiers,
    result types, and queries.
    """
    id = HiddenField("Study ID", default=0)  # Hidden field for study ID
    name = StringField("Study name", [validators.InputRequired("Input required.")])  # Required study name
    description = TextAreaField("Description")  # Field for study description
    type = SelectField("Study type", coerce=int)  # Dropdown for selecting study type
    imported = BooleanField("Import own search results", default=False)  # Checkbox for importing search results
    imported_data = FileField("Add own search results (csv)")  # File upload for search results
    search_engines = MultiCheckboxField("Select search engines", coerce=int)  # Multiple checkbox field for search engines
    classifier = MultiCheckboxField("Select classifier", coerce=int)  # Multiple checkbox field for classifiers
    result_type = SelectField("Select result types", choices=[(1, "Organic Results"),
                                                               (2, "Snippets"),
                                                               (3, "Universal Search Results"),
                                                               (4, "Advertisements")], coerce=int)  # Dropdown for result types
    queries = TextAreaField("Queries (use new line for each query)", validators=[validators.Length(min=1, max=50000, message="Please enter at least one query.")])  # Text area for entering queries
    query_list = FileField("List of queries (csv)")  # File upload for list of queries
    task = StringField("Search Task (use *** as a placeholder for the query)", default="In the following, you see the results for the query ***. Please assess the results using the questions below.")  # Field for describing the search task
    result_count = IntegerField("Number of results to collect", default=10, validators=[validators.NumberRange(min=1, max=200, message="The number of results can be between 1 and 200.")])  # Integer field for specifying the number of results
    submit = SubmitField("Create study")  # Submit button


class MonitoringForm(FlaskForm):
    """
    Form for creating or editing a monitoring task.

    Includes fields for monitoring details, queries, countries, result counts,
    and frequency settings.
    """
    name = StringField("Monitoring name")  # Field for monitoring name
    description = TextAreaField("Monitoring description")  # Field for monitoring description
    queries = TextAreaField("Queries (use new line for each query)")  # Text area for entering queries
    countries = MultiCheckboxField("Select countries", coerce=int)  # Multiple checkbox field for selecting countries
    result_count = IntegerField("Number of results to collect")  # Integer field for specifying the number of results
    result_type = SelectField("Select result types", choices=[(2, "Snippets")], coerce=int)  # Dropdown for result types
    interval_frequency = SelectField("Frequency", choices=[(1, "once"), (2, "twice")])  # Dropdown for frequency
    interval_mode = SelectField("Mode", choices=[(1, "daily"), (2, "weekly"), (3, "monthly")], coerce=int)  # Dropdown for mode
    submit = SubmitField("Create monitoring")  # Submit button


class ConfirmationForm(FlaskForm):
    """
    Form for confirming an action.

    Includes a hidden field and a submit button.
    """
    data = HiddenField("Data")  # Hidden field for storing data
    submit = SubmitField("Confirm")  # Submit button


class AnswerOptions(FlaskForm):
    """
    Form for defining options for a question.

    Includes fields for value and label of the options.
    """
    value = StringField("Value")  # Field for option value
    label = StringField("Label")  # Field for option label


class RangeOptions(FlaskForm):
    """
    Form for defining range options for a question.

    Includes fields for start value, end value, step, and text labels.
    """
    start = IntegerField("Starting Value", default=0)  # Integer field for starting value
    stop = IntegerField("End Value", default=100)  # Integer field for end value
    step = DecimalField("Steps", default=1)  # Decimal field for step size
    start_text = StringField("Start Text")  # Field for start text
    stop_text = StringField("Stop Text")  # Field for stop text


class QuestionForm(FlaskForm):
    """
    Form for creating or editing a question.

    Includes fields for question type, text, options, and ranges.
    """
    q_type = SelectField("Question type")  # Dropdown for selecting question type
    text = StringField("Question")  # Field for question text
    position = IntegerField("Question number")  # Integer field for question number
    options = FieldList(FormField(AnswerOptions), min_entries=2, label="Answer Options")  # Field list for answer options
    ranges = FieldList(FormField(RangeOptions), min_entries=1, label="Range Options")  # Field list for range options
    submit = SubmitField("Create question")  # Submit button


class AnswerForm(FlaskForm):
    """
    Form for submitting answers to questions.

    Includes fields for different types of answers.
    """
    short_text = StringField("Answer")  # Field for short text answers
    long_text = TextAreaField("Answer")  # Field for long text answers
    true_false = RadioField("Answer", coerce=int)  # Radio field for true/false answers
    likert_scale = RadioField("Answer", coerce=int)  # Radio field for Likert scale answers
    multiple_choice = MultiCheckboxField("Answer", coerce=int)  # Multiple checkbox field for multiple choice answers
    scale_number = IntegerRangeField("Answer")  # Field for scale number answers
    submit = SubmitField("Next")  # Submit button
    skip = SubmitField("Skip")  # Skip button


class EvaluationForm(FlaskForm):
    """
    Form for evaluating something with a status and comments.

    Includes fields for status and comments.
    """
    status = RadioField("Status", choices=[(1, "OK"), (0, "Not OK")], coerce=int)  # Radio field for status
    comment = TextAreaField("Comment")  # Field for additional comments
    submit = SubmitField("Submit")  # Submit button


class JoinForm(FlaskForm):
    """
    Form for joining, either as a new user or returning user.

    Includes submit buttons for both new and returning users.
    """
    new = SubmitField("New")  # Button for new users
    returning = SubmitField("Returning")  # Button for returning users


class ParticipantLogInForm(FlaskForm):
    """
    Form for participant login.

    Includes fields for username, password, and login button.
    """
    username = StringField("Username")  # Field for username
    password = PasswordField("Code")  # Field for password
    submit = SubmitField("Log in")  # Submit button


class ExportForm(FlaskForm):
    """
    Form for exporting data.

    Includes a radio field to select data and a submit button.
    """
    tables = RadioField("Select data to export:", coerce=int)  # Radio field for selecting data to export
    submit = SubmitField("Generate Excel")  # Submit button


class ContactForm(FlaskForm):
    """
    Form for contacting support or sending a message.

    Includes fields for name, email, message, and submit button.
    """
    name = StringField("Name")  # Field for name
    email = EmailField("E-Mail")  # Field for email
    message = TextAreaField("Message")  # Field for message
    submit = SubmitField("Send")  # Submit button
